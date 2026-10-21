"""Research entry point.

An unconfigured process still refuses to invent a guide. A configured process
searches, reads public pages, and saves a guide only after the draft validates.
"""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import EvidenceRecord, ResearchRun
from app.research.errors import InvalidAppName, RunInProgress, UnsafeURL
from app.research.identify import find_existing, interpret
from app.research.pipeline import execute_run
from app.research.stream import stream_events
from app.schemas import (
    EvidenceView,
    GuideExistsResponse,
    ResearchAccepted,
    ResearchRequest,
    ResearchRunView,
    ResearchUnavailable,
)

router = APIRouter(tags=["research"])


def _accepted(run: ResearchRun) -> ResearchAccepted:
    slug = run.guide_slug
    return ResearchAccepted(
        code="research_started",
        run_id=run.id,
        app_name=run.app_name,
        events_url=f"/api/research-runs/{run.id}/events",
        status=run.status,
        guide_created=run.guide_created,
        guide_url=f"/guides/{slug}" if slug else None,
        slug=slug,
    )


@router.post("/research-requests")
def submit_research(
    body: ResearchRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> JSONResponse:
    docs_url = str(body.docs_url) if body.docs_url else None
    try:
        identity = interpret(body.app_name, docs_url)
    except (UnsafeURL, InvalidAppName) as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message}) from exc

    guide = find_existing(session, identity)
    if guide is not None:
        payload = GuideExistsResponse(
            code="guide_exists",
            app_name=guide.name,
            slug=guide.slug,
            guide_url=f"/guides/{guide.slug}",
            guide_created=False,
        )
        return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))

    deps = request.app.state.research
    if deps.configured and not identity.docs_url:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "docs_url_required",
                "message": (
                    "Add the documentation URL. Research reads at most four pages, "
                    "and a URL keeps those pages on this app. No guide was saved."
                ),
            },
        )
    if not deps.configured:
        payload = ResearchUnavailable(
            code="research_unavailable",
            message=deps.unavailable_reason
            or "Live research is not configured. This request did not create a guide.",
            app_name=identity.app_name,
            docs_url=identity.docs_url,
            guide_created=False,
        )
        return JSONResponse(status_code=503, content=payload.model_dump(mode="json"))

    try:
        run = start_and_launch(session, request, identity)
    except RunInProgress as exc:
        current = session.get(ResearchRun, exc.run_id)
        if current is None:
            raise HTTPException(status_code=409, detail={"code": "research_in_progress", "message": "A run is already in progress."}) from exc
        payload = ResearchAccepted(
            code="research_in_progress",
            run_id=current.id,
            app_name=current.app_name,
            events_url=f"/api/research-runs/{current.id}/events",
            status=current.status,
            guide_created=current.guide_created,
            guide_url=f"/guides/{current.guide_slug}" if current.guide_slug else None,
            slug=current.guide_slug,
        )
        return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))

    session.expire_all()
    fresh = session.get(ResearchRun, run.id)
    body_out = _accepted(fresh or run)
    return JSONResponse(status_code=202, content=body_out.model_dump(mode="json"))


def start_and_launch(
    session: Session,
    request: Request,
    identity,
    *,
    purpose: str = "create",
    target_slug: str | None = None,
):
    from app.research.store import start_run

    run = start_run(session, identity, purpose=purpose, target_slug=target_slug)
    deps = request.app.state.research
    factory = request.app.state.session_factory
    if deps.inline:
        execute_run(factory, run.id, deps)
    else:
        thread = threading.Thread(
            target=execute_run,
            args=(factory, run.id, deps),
            name=f"research-{run.id}",
            daemon=True,
        )
        thread.start()
    return run


@router.get("/research-runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)) -> ResearchRunView:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "No research run exists for this address."},
        )
    evidence = session.scalars(
        select(EvidenceRecord).where(EvidenceRecord.run_id == run_id).order_by(EvidenceRecord.id.asc())
    ).all()
    return ResearchRunView(
        id=run.id,
        app_name=run.app_name,
        status=run.status,
        stage=run.stage,
        error_code=run.error_code,
        message=run.message,
        guide_slug=run.guide_slug,
        guide_url=f"/guides/{run.guide_slug}" if run.guide_slug else None,
        guide_created=run.guide_created,
        evidence=[
            EvidenceView(
                evidence_key=item.evidence_key,
                url=item.url,
                title=item.title,
                retrieved_at=item.retrieved_at.isoformat(),
                supports=_supports(item.supports_json),
            )
            for item in evidence
        ],
    )


@router.get("/research-runs/{run_id}/events")
def run_events(run_id: str, request: Request, session: Session = Depends(get_session)) -> StreamingResponse:
    if session.get(ResearchRun, run_id) is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "No research run exists for this address."},
        )
    header = request.headers.get("last-event-id", "0")
    try:
        after_id = int(header)
    except ValueError:
        after_id = 0
    return StreamingResponse(
        stream_events(request.app.state.session_factory, run_id, after_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _supports(raw: str) -> list[str]:
    import json

    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, str)]
