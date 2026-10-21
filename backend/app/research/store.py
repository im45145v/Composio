"""Persist research runs, evidence, and guides. Existing guides are not replaced."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ActiveResearch, EvidenceRecord, Guide, GuideItem, ResearchEvent, ResearchRun, Source
from app.research.errors import RunInProgress
from app.research.identify import Identity
from app.research.validate import CheckedClaim, CheckedGuide

EXECUTION_NOTE = (
    "No OAuth flow was executed for this guide. Documented claims are statements in pages "
    "retrieved for this run. Inferred claims are a reading of those pages, not a direct statement. "
    "Unknown means the retrieved pages did not establish it. Verified is reserved for a setup this "
    "project has run, and research does not use it."
)
TERMINAL = {"completed", "failed", "insufficient_evidence", "existing_guide"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def start_run(session: Session, identity: Identity) -> ResearchRun:
    lock = session.get(ActiveResearch, identity.normalized_name)
    if lock is not None:
        current = session.get(ResearchRun, lock.run_id)
        if current is not None and current.status in {"queued", "running"}:
            raise RunInProgress(current.id)
        session.delete(lock)
        session.flush()

    run = ResearchRun(
        id=str(uuid4()),
        app_name=identity.app_name,
        normalized_name=identity.normalized_name,
        docs_url=identity.docs_url,
        status="queued",
        stage="accepted",
        error_code=None,
        message=None,
        guide_slug=None,
        guide_created=False,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    session.add(run)
    session.add(ActiveResearch(normalized_name=identity.normalized_name, run_id=run.id))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raced = session.get(ActiveResearch, identity.normalized_name)
        if raced is not None:
            raise RunInProgress(raced.run_id) from None
        raise
    return run


def emit(session: Session, run: ResearchRun, stage: str, message: str, **payload: object) -> ResearchEvent:
    clean = " ".join(message.split())
    event = ResearchEvent(
        run_id=run.id,
        stage=stage,
        message=clean,
        payload_json=json.dumps(payload, default=str) if payload else None,
        created_at=utcnow(),
    )
    run.stage = stage
    run.updated_at = utcnow()
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def release_lock(session: Session, run: ResearchRun) -> None:
    lock = session.get(ActiveResearch, run.normalized_name)
    if lock is not None and lock.run_id == run.id:
        session.delete(lock)


def finish(
    session: Session,
    run: ResearchRun,
    status: str,
    message: str,
    *,
    code: str | None = None,
    slug: str | None = None,
    created: bool = False,
) -> None:
    if run.status in TERMINAL:
        release_lock(session, run)
        session.commit()
        return
    run.status = status
    run.error_code = code
    run.message = message
    run.guide_slug = slug
    run.guide_created = created
    release_lock(session, run)
    emit(
        session,
        run,
        status,
        message,
        status=status,
        code=code,
        slug=slug,
        guide_url=f"/guides/{slug}" if slug else None,
        guide_created=created,
    )


def add_evidence(
    session: Session,
    run: ResearchRun,
    *,
    key: str,
    url: str,
    title: str,
    retrieved_at: datetime,
    excerpt: str,
) -> None:
    session.add(
        EvidenceRecord(
            run_id=run.id,
            evidence_key=key,
            url=url[:500],
            title=title[:200],
            retrieved_at=retrieved_at,
            excerpt=excerpt[:8000],
            supports_json="[]",
        )
    )


def set_supports(session: Session, run_id: str, supports: dict[str, list[str]]) -> None:
    rows = session.scalars(select(EvidenceRecord).where(EvidenceRecord.run_id == run_id)).all()
    for row in rows:
        row.supports_json = json.dumps(supports.get(row.evidence_key, []))


def _text(claim: CheckedClaim) -> str:
    return claim.value if claim.value else "Unknown"


def _publisher(url: str) -> str:
    return (urlsplit(url).hostname or "source")[:80]


def persist_guide(
    session: Session,
    identity: Identity,
    checked: CheckedGuide,
    pages: list,
) -> tuple[str, bool]:
    """Insert a guide. If the slug already exists, leave that row unchanged."""

    existing = session.scalar(select(Guide).where(Guide.slug == identity.normalized_name))
    if existing is not None:
        return existing.slug, False

    today = utcnow().date()
    guide = Guide(
        slug=identity.normalized_name,
        name=identity.app_name,
        summary=checked.summary,
        auth_type_value=_text(checked.auth_type),
        auth_type_status=checked.auth_type.status,
        auth_type_note=checked.auth_type.note,
        setup_path=checked.setup_path_value,
        setup_path_label=checked.setup_path_label,
        setup_path_status=checked.setup_path_status,
        setup_path_note=checked.setup_path_note,
        difficulty_value=_text(checked.difficulty),
        difficulty_status=checked.difficulty.status,
        difficulty_note=checked.difficulty.note,
        active_effort_value=_text(checked.active_effort),
        active_effort_status=checked.active_effort.status,
        active_effort_note=checked.active_effort.note,
        approval_wait_value=_text(checked.approval_wait),
        approval_wait_status=checked.approval_wait.status,
        approval_wait_note=checked.approval_wait.note,
        confidence_value=_text(checked.confidence),
        confidence_status=checked.confidence.status,
        confidence_note=checked.confidence.note,
        managed_value=_text(checked.managed),
        managed_status=checked.managed.status,
        managed_note=checked.managed.note,
        byo_value=_text(checked.bring_your_own),
        byo_status=checked.bring_your_own.status,
        byo_note=checked.bring_your_own.note,
        redirect_value=_text(checked.redirect_uri),
        redirect_status=checked.redirect_uri.status,
        redirect_note=checked.redirect_uri.note,
        decision=checked.decision,
        execution_note=EXECUTION_NOTE,
        tested=False,
        last_checked=today,
    )
    try:
        with session.begin_nested():
            session.add(guide)
            session.flush()
    except IntegrityError:
        found = session.scalar(select(Guide).where(Guide.slug == identity.normalized_name))
        if found is None:
            raise
        return found.slug, False

    groups = (
        ("prerequisite", checked.prerequisites),
        ("step", checked.steps),
        ("blocker", checked.blockers),
        ("human_action", checked.human_actions),
    )
    for kind, items in groups:
        for position, item in enumerate(items, start=1):
            guide.items.append(
                GuideItem(
                    kind=kind,
                    position=position,
                    title=item.title[:200],
                    body=item.body,
                    status=item.status,
                    note=item.note,
                )
            )

    cited = {page.key for page in pages if checked.supports.get(page.key)}
    ordered = [page for page in pages if page.key in cited] or list(pages)
    for position, page in enumerate(ordered, start=1):
        guide.sources.append(
            Source(
                position=position,
                title=page.title[:200],
                url=page.url[:500],
                publisher=_publisher(page.url),
                accessed_on=page.retrieved_at.date(),
            )
        )
    session.flush()
    return guide.slug, True
