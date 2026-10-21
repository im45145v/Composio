"""Guide directory endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_session
from app.models import Guide, GuideCandidate, ResearchRun
from app.research.errors import InvalidAppName, RunInProgress, UnsafeURL
from app.research.identify import Identity
from app.research.safety import screen_url
from app.schemas import (
    CandidateView,
    GuideDetail,
    GuideListResponse,
    PendingCandidate,
    RecheckRequest,
    ResearchAccepted,
    ResearchUnavailable,
)
from app.seed import SETUP_PATHS
from app.serialize import guide_detail, guide_summary

router = APIRouter(tags=["guides"])


@router.get("/guides", response_model=GuideListResponse)
def list_guides(
    q: str | None = Query(default=None, max_length=120),
    path: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> GuideListResponse:
    if path is not None and path not in SETUP_PATHS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_path",
                "message": "Unknown setup path filter.",
                "allowed": sorted(SETUP_PATHS),
            },
        )

    statement = select(Guide).order_by(Guide.name.asc())
    needle = (q or "").strip().lower()
    if needle:
        like = f"%{needle}%"
        statement = statement.where(
            or_(
                func.lower(Guide.name).like(like),
                func.lower(Guide.slug).like(like),
                func.lower(Guide.summary).like(like),
            )
        )
    if path is not None:
        statement = statement.where(Guide.setup_path == path)

    guides = session.scalars(statement).all()
    summaries = [guide_summary(guide) for guide in guides]
    return GuideListResponse(guides=summaries, count=len(summaries))


@router.get("/guides/{slug}", response_model=GuideDetail)
def get_guide(slug: str, session: Session = Depends(get_session)) -> GuideDetail:
    guide = _load_guide(session, slug)
    return guide_detail(guide, _pending(session, guide.slug))


def _load_guide(session: Session, slug: str) -> Guide:
    statement = (
        select(Guide)
        .where(Guide.slug == slug)
        .options(selectinload(Guide.items), selectinload(Guide.sources))
    )
    guide = session.scalar(statement)
    if guide is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "not_found",
                "message": "No guide exists for this address.",
                "slug": slug,
            },
        )
    return guide


def _pending(session: Session, slug: str) -> PendingCandidate | None:
    row = session.scalar(
        select(GuideCandidate)
        .where(GuideCandidate.guide_slug == slug, GuideCandidate.status == "pending")
        .order_by(GuideCandidate.created_at.desc())
    )
    if row is None:
        return None
    return PendingCandidate(id=row.id, run_id=row.run_id, created_at=row.created_at.isoformat())


def _pending_row(session: Session, slug: str) -> GuideCandidate:
    row = session.scalar(
        select(GuideCandidate)
        .where(GuideCandidate.guide_slug == slug, GuideCandidate.status == "pending")
        .order_by(GuideCandidate.created_at.desc())
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "no_candidate",
                "message": "This guide has no recheck waiting.",
                "slug": slug,
            },
        )
    return row


@router.post("/guides/{slug}/recheck")
def recheck_guide(
    slug: str,
    body: RecheckRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Read the docs again and store a candidate. The live guide stays until promotion."""

    guide = _load_guide(session, slug)
    deps = request.app.state.research
    docs_url = str(body.docs_url) if body.docs_url else None
    if not deps.configured:
        payload = ResearchUnavailable(
            code="research_unavailable",
            message=deps.unavailable_reason
            or "Live research is not configured. This request did not create a guide.",
            app_name=guide.name,
            docs_url=docs_url,
            guide_created=False,
        )
        return JSONResponse(status_code=503, content=payload.model_dump(mode="json"))
    if not docs_url:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "docs_url_required",
                "message": (
                    "Add the documentation URL. A recheck reads at most four pages, "
                    "and a URL keeps those pages on this app. The live guide was not changed."
                ),
            },
        )
    try:
        screened = screen_url(docs_url)
    except UnsafeURL as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message}) from exc
    identity = Identity(
        app_name=guide.name,
        normalized_name=guide.slug,
        docs_url=screened,
        matched_slug=guide.slug,
    )
    from app.routers.research import start_and_launch

    try:
        run = start_and_launch(session, request, identity, purpose="recheck", target_slug=guide.slug)
    except RunInProgress as exc:
        current = session.get(ResearchRun, exc.run_id)
        if current is None:
            raise HTTPException(
                status_code=409,
                detail={"code": "research_in_progress", "message": "A run is already in progress."},
            ) from exc
        payload = ResearchAccepted(
            code="research_in_progress",
            run_id=current.id,
            app_name=current.app_name,
            events_url=f"/api/research-runs/{current.id}/events",
            status=current.status,
            guide_created=False,
            guide_url=f"/guides/{guide.slug}",
            slug=guide.slug,
        )
        return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))
    except InvalidAppName as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message}) from exc

    session.expire_all()
    fresh = session.get(ResearchRun, run.id) or run
    payload = ResearchAccepted(
        code="research_started",
        run_id=fresh.id,
        app_name=fresh.app_name,
        events_url=f"/api/research-runs/{fresh.id}/events",
        status=fresh.status,
        guide_created=False,
        guide_url=f"/guides/{guide.slug}",
        slug=guide.slug,
    )
    return JSONResponse(status_code=202, content=payload.model_dump(mode="json"))


@router.get("/guides/{slug}/candidate", response_model=CandidateView)
def get_candidate(slug: str, session: Session = Depends(get_session)) -> CandidateView:
    guide = _load_guide(session, slug)
    row = _pending_row(session, slug)
    payload = json.loads(row.payload_json)
    from app.research.store import changed_field_labels, guide_from_payload

    proposed = guide_from_payload(slug, payload)
    return CandidateView(
        id=row.id,
        run_id=row.run_id,
        created_at=row.created_at.isoformat(),
        changed_fields=changed_field_labels(guide, payload),
        guide=guide_detail(proposed),
    )


@router.post("/guides/{slug}/candidate/promote", response_model=GuideDetail)
def promote_candidate(slug: str, session: Session = Depends(get_session)) -> GuideDetail:
    guide = _load_guide(session, slug)
    row = _pending_row(session, slug)
    payload = json.loads(row.payload_json)
    from app.research.store import apply_payload

    apply_payload(session, guide, payload)
    row.status = "promoted"
    session.commit()
    session.expire_all()
    fresh = _load_guide(session, slug)
    return guide_detail(fresh, None)


@router.post("/guides/{slug}/candidate/discard")
def discard_candidate(slug: str, session: Session = Depends(get_session)) -> dict[str, str]:
    _load_guide(session, slug)
    row = _pending_row(session, slug)
    row.status = "discarded"
    session.commit()
    return {"status": "discarded", "slug": slug}
