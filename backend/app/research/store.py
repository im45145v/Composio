"""Persist research runs, evidence, and guides. Existing guides are not replaced."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ActiveResearch,
    EvidenceRecord,
    Guide,
    GuideCandidate,
    GuideItem,
    ResearchEvent,
    ResearchRun,
    Source,
)
from app.research.errors import RunInProgress
from app.research.identify import Identity
from app.research.validate import CheckedClaim, CheckedGuide

EXECUTION_NOTE = (
    "No OAuth flow was executed for this guide. Documented claims are statements in pages "
    "retrieved for this run. Inferred claims are a reading of those pages, not a direct statement. "
    "Unknown means the retrieved pages did not establish it. Verified is reserved for a setup this "
    "project has run, and research does not use it."
)
TERMINAL = {"completed", "failed", "insufficient_evidence", "existing_guide", "candidate_ready"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def abandon_interrupted_runs(session_factory) -> None:
    """A restart kills the background thread. Release the name so the app can be researched again."""

    with session_factory() as session:
        runs = session.scalars(
            select(ResearchRun).where(ResearchRun.status.in_(("queued", "running")))
        ).all()
        for run in list(runs):
            finish(
                session,
                run,
                "failed",
                "The research process restarted before this run finished, so no guide was saved.",
                code="interrupted",
            )
        for lock in session.scalars(select(ActiveResearch)).all():
            current = session.get(ResearchRun, lock.run_id)
            if current is None or current.status in TERMINAL:
                session.delete(lock)
        session.commit()


def start_run(
    session: Session,
    identity: Identity,
    *,
    purpose: str = "create",
    target_slug: str | None = None,
) -> ResearchRun:
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
        purpose=purpose,
        target_slug=target_slug,
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


def _first_url(evidence_ids: list[str], pages: list) -> str | None:
    by_key = {page.key: page.url for page in pages}
    for evidence_id in evidence_ids:
        url = by_key.get(evidence_id)
        if url:
            return url[:500]
    return None


def _cited_sources(checked: CheckedGuide, pages: list) -> dict[str, str]:
    cited: dict[str, str] = {}
    claims = {
        "auth_type": checked.auth_type,
        "setup_path": checked,
        "difficulty": checked.difficulty,
        "active_effort": checked.active_effort,
        "approval_wait": checked.approval_wait,
        "confidence": checked.confidence,
        "managed": checked.managed,
        "bring_your_own": checked.bring_your_own,
        "redirect_uri": checked.redirect_uri,
    }
    for key, claim in claims.items():
        if key == "setup_path":
            status = checked.setup_path_status
            evidence_ids = checked.setup_path_evidence_ids
        else:
            status = claim.status
            evidence_ids = claim.evidence_ids
        if status == "unknown":
            continue
        url = _first_url(evidence_ids, pages)
        if url:
            cited[key] = url
    return cited


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
        origin="researched",
        last_checked=today,
        claim_sources_json=json.dumps(_cited_sources(checked, pages)),
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
                    source_url=_first_url(item.evidence_ids, pages) if item.status != "unknown" else None,
                    audience="shared",
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


def _snapshot(identity: Identity, checked: CheckedGuide, pages: list) -> dict:
    today = utcnow().date()
    items = []
    groups = (
        ("prerequisite", checked.prerequisites),
        ("step", checked.steps),
        ("blocker", checked.blockers),
        ("human_action", checked.human_actions),
    )
    for kind, rows in groups:
        for position, item in enumerate(rows, start=1):
            items.append(
                {
                    "kind": kind,
                    "position": position,
                    "title": item.title[:200],
                    "body": item.body,
                    "status": item.status,
                    "note": item.note,
                    "source_url": _first_url(item.evidence_ids, pages) if item.status != "unknown" else None,
                    "audience": "shared",
                }
            )
    cited = {page.key for page in pages if checked.supports.get(page.key)}
    ordered = [page for page in pages if page.key in cited] or list(pages)
    sources = [
        {
            "position": position,
            "title": page.title[:200],
            "url": page.url[:500],
            "publisher": _publisher(page.url),
            "accessed_on": page.retrieved_at.date().isoformat(),
        }
        for position, page in enumerate(ordered, start=1)
    ]
    return {
        "name": identity.app_name,
        "summary": checked.summary,
        "decision": checked.decision,
        "execution_note": EXECUTION_NOTE,
        "auth_type_value": _text(checked.auth_type),
        "auth_type_status": checked.auth_type.status,
        "auth_type_note": checked.auth_type.note,
        "setup_path": checked.setup_path_value,
        "setup_path_label": checked.setup_path_label,
        "setup_path_status": checked.setup_path_status,
        "setup_path_note": checked.setup_path_note,
        "difficulty_value": _text(checked.difficulty),
        "difficulty_status": checked.difficulty.status,
        "difficulty_note": checked.difficulty.note,
        "active_effort_value": _text(checked.active_effort),
        "active_effort_status": checked.active_effort.status,
        "active_effort_note": checked.active_effort.note,
        "approval_wait_value": _text(checked.approval_wait),
        "approval_wait_status": checked.approval_wait.status,
        "approval_wait_note": checked.approval_wait.note,
        "confidence_value": _text(checked.confidence),
        "confidence_status": checked.confidence.status,
        "confidence_note": checked.confidence.note,
        "managed_value": _text(checked.managed),
        "managed_status": checked.managed.status,
        "managed_note": checked.managed.note,
        "byo_value": _text(checked.bring_your_own),
        "byo_status": checked.bring_your_own.status,
        "byo_note": checked.bring_your_own.note,
        "redirect_value": _text(checked.redirect_uri),
        "redirect_status": checked.redirect_uri.status,
        "redirect_note": checked.redirect_uri.note,
        "claim_sources": _cited_sources(checked, pages),
        "items": items,
        "sources": sources,
        "last_checked": today.isoformat(),
        "origin": "researched",
        "tested": False,
    }


def changed_field_labels(guide: Guide, payload: dict) -> list[str]:
    labels: list[str] = []
    checks = (
        ("Decision", guide.decision, payload.get("decision")),
        ("Summary", guide.summary, payload.get("summary")),
        ("Redirect URI", guide.redirect_value, payload.get("redirect_value")),
        ("Approval wait", guide.approval_wait_value, payload.get("approval_wait_value")),
        ("Managed auth", guide.managed_value, payload.get("managed_value")),
        ("Your own app", guide.byo_value, payload.get("byo_value")),
        ("Setup path", guide.setup_path, payload.get("setup_path")),
    )
    for label, current, proposed in checks:
        if (current or "") != (proposed or ""):
            labels.append(label)
    if len(guide.items) != len(payload.get("items") or []):
        labels.append("Steps and notes")
    return labels


def persist_candidate(
    session: Session,
    slug: str,
    run_id: str,
    identity: Identity,
    checked: CheckedGuide,
    pages: list,
) -> GuideCandidate:
    """Store a recheck beside the live guide. Older pending candidates are discarded."""

    pending = session.scalars(
        select(GuideCandidate).where(
            GuideCandidate.guide_slug == slug,
            GuideCandidate.status == "pending",
        )
    ).all()
    for older in pending:
        older.status = "discarded"
    candidate = GuideCandidate(
        id=str(uuid4()),
        guide_slug=slug,
        run_id=run_id,
        status="pending",
        payload_json=json.dumps(_snapshot(identity, checked, pages)),
        created_at=utcnow(),
    )
    session.add(candidate)
    session.flush()
    return candidate


def guide_from_payload(slug: str, payload: dict) -> Guide:
    from datetime import date as date_cls

    guide = Guide(
        slug=slug,
        name=payload["name"],
        summary=payload["summary"],
        decision=payload["decision"],
        execution_note=payload["execution_note"],
        auth_type_value=payload["auth_type_value"],
        auth_type_status=payload["auth_type_status"],
        auth_type_note=payload.get("auth_type_note"),
        setup_path=payload["setup_path"],
        setup_path_label=payload["setup_path_label"],
        setup_path_status=payload["setup_path_status"],
        setup_path_note=payload.get("setup_path_note"),
        difficulty_value=payload["difficulty_value"],
        difficulty_status=payload["difficulty_status"],
        difficulty_note=payload.get("difficulty_note"),
        active_effort_value=payload["active_effort_value"],
        active_effort_status=payload["active_effort_status"],
        active_effort_note=payload.get("active_effort_note"),
        approval_wait_value=payload["approval_wait_value"],
        approval_wait_status=payload["approval_wait_status"],
        approval_wait_note=payload.get("approval_wait_note"),
        confidence_value=payload["confidence_value"],
        confidence_status=payload["confidence_status"],
        confidence_note=payload.get("confidence_note"),
        managed_value=payload["managed_value"],
        managed_status=payload["managed_status"],
        managed_note=payload.get("managed_note"),
        byo_value=payload["byo_value"],
        byo_status=payload["byo_status"],
        byo_note=payload.get("byo_note"),
        redirect_value=payload["redirect_value"],
        redirect_status=payload["redirect_status"],
        redirect_note=payload.get("redirect_note"),
        tested=bool(payload.get("tested")),
        origin=payload.get("origin") or "researched",
        last_checked=date_cls.fromisoformat(payload["last_checked"]),
        claim_sources_json=json.dumps(payload.get("claim_sources") or {}),
    )
    guide.items = [
        GuideItem(
            kind=item["kind"],
            position=item["position"],
            title=item["title"],
            body=item["body"],
            status=item["status"],
            note=item.get("note"),
            source_url=item.get("source_url"),
            audience=item.get("audience") or "shared",
        )
        for item in payload.get("items") or []
    ]
    guide.sources = [
        Source(
            position=source["position"],
            title=source["title"],
            url=source["url"],
            publisher=source["publisher"],
            accessed_on=date_cls.fromisoformat(source["accessed_on"]),
        )
        for source in payload.get("sources") or []
    ]
    return guide


def apply_payload(session: Session, guide: Guide, payload: dict) -> None:
    from datetime import date as date_cls

    guide.name = payload["name"]
    guide.summary = payload["summary"]
    guide.decision = payload["decision"]
    guide.execution_note = payload["execution_note"]
    guide.auth_type_value = payload["auth_type_value"]
    guide.auth_type_status = payload["auth_type_status"]
    guide.auth_type_note = payload.get("auth_type_note")
    guide.setup_path = payload["setup_path"]
    guide.setup_path_label = payload["setup_path_label"]
    guide.setup_path_status = payload["setup_path_status"]
    guide.setup_path_note = payload.get("setup_path_note")
    guide.difficulty_value = payload["difficulty_value"]
    guide.difficulty_status = payload["difficulty_status"]
    guide.difficulty_note = payload.get("difficulty_note")
    guide.active_effort_value = payload["active_effort_value"]
    guide.active_effort_status = payload["active_effort_status"]
    guide.active_effort_note = payload.get("active_effort_note")
    guide.approval_wait_value = payload["approval_wait_value"]
    guide.approval_wait_status = payload["approval_wait_status"]
    guide.approval_wait_note = payload.get("approval_wait_note")
    guide.confidence_value = payload["confidence_value"]
    guide.confidence_status = payload["confidence_status"]
    guide.confidence_note = payload.get("confidence_note")
    guide.managed_value = payload["managed_value"]
    guide.managed_status = payload["managed_status"]
    guide.managed_note = payload.get("managed_note")
    guide.byo_value = payload["byo_value"]
    guide.byo_status = payload["byo_status"]
    guide.byo_note = payload.get("byo_note")
    guide.redirect_value = payload["redirect_value"]
    guide.redirect_status = payload["redirect_status"]
    guide.redirect_note = payload.get("redirect_note")
    guide.tested = False
    guide.origin = "researched"
    guide.last_checked = date_cls.fromisoformat(payload["last_checked"])
    guide.claim_sources_json = json.dumps(payload.get("claim_sources") or {})
    guide.items.clear()
    guide.sources.clear()
    session.flush()
    for item in payload.get("items") or []:
        guide.items.append(
            GuideItem(
                kind=item["kind"],
                position=item["position"],
                title=item["title"],
                body=item["body"],
                status=item["status"],
                note=item.get("note"),
                source_url=item.get("source_url"),
                audience=item.get("audience") or "shared",
            )
        )
    for source in payload.get("sources") or []:
        guide.sources.append(
            Source(
                position=source["position"],
                title=source["title"],
                url=source["url"],
                publisher=source["publisher"],
                accessed_on=date_cls.fromisoformat(source["accessed_on"]),
            )
        )
