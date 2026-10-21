"""Map database rows onto the public API models."""

from __future__ import annotations

import json

from app.models import Guide, GuideItem
from app.schemas import (
    ClaimModel,
    ComposioSection,
    GuideDetail,
    GuideItemModel,
    GuideSummary,
    PendingCandidate,
    SetupPathModel,
    SourceModel,
)


def _claim(value: str, status: str, note: str | None, source_url: str | None = None) -> ClaimModel:
    shown: str | None = value
    if status == "unknown" and value.strip().lower() == "unknown":
        shown = None
    return ClaimModel(value=shown, status=status, note=note, source_url=source_url)


def _claim_sources(guide: Guide) -> dict[str, str]:
    try:
        parsed = json.loads(guide.claim_sources_json or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {key: url for key, url in parsed.items() if isinstance(key, str) and isinstance(url, str)}


def _items(guide: Guide, kind: str) -> list[GuideItemModel]:
    rows: list[GuideItem] = [item for item in guide.items if item.kind == kind]
    rows.sort(key=lambda item: item.position)
    return [
        GuideItemModel(
            position=item.position,
            title=item.title,
            body=item.body,
            status=item.status,
            note=item.note,
            source_url=item.source_url,
            audience=item.audience if item.audience in {"managed", "own", "shared"} else "shared",
        )
        for item in rows
    ]


def guide_summary(guide: Guide) -> GuideSummary:
    sources = _claim_sources(guide)
    return GuideSummary(
        slug=guide.slug,
        name=guide.name,
        summary=guide.summary,
        decision=guide.decision,
        origin="researched" if guide.origin == "researched" else "editorial",
        auth_type=_claim(
            guide.auth_type_value,
            guide.auth_type_status,
            guide.auth_type_note,
            sources.get("auth_type"),
        ),
        setup_path=SetupPathModel(
            value=guide.setup_path,
            label=guide.setup_path_label,
            status=guide.setup_path_status,
            note=guide.setup_path_note,
            source_url=sources.get("setup_path"),
        ),
        difficulty=_claim(
            guide.difficulty_value,
            guide.difficulty_status,
            guide.difficulty_note,
            sources.get("difficulty"),
        ),
        active_effort=_claim(
            guide.active_effort_value,
            guide.active_effort_status,
            guide.active_effort_note,
            sources.get("active_effort"),
        ),
        approval_wait=_claim(
            guide.approval_wait_value,
            guide.approval_wait_status,
            guide.approval_wait_note,
            sources.get("approval_wait"),
        ),
        confidence=_claim(
            guide.confidence_value,
            guide.confidence_status,
            guide.confidence_note,
            sources.get("confidence"),
        ),
        tested=guide.tested,
        last_checked=guide.last_checked,
    )


def guide_detail(guide: Guide, pending: PendingCandidate | None = None) -> GuideDetail:
    summary = guide_summary(guide)
    sources = _claim_sources(guide)
    return GuideDetail(
        **summary.model_dump(),
        execution_note=guide.execution_note,
        composio=ComposioSection(
            decision=guide.decision,
            managed=_claim(
                guide.managed_value,
                guide.managed_status,
                guide.managed_note,
                sources.get("managed"),
            ),
            bring_your_own=_claim(
                guide.byo_value,
                guide.byo_status,
                guide.byo_note,
                sources.get("bring_your_own"),
            ),
            redirect_uri=_claim(
                guide.redirect_value,
                guide.redirect_status,
                guide.redirect_note,
                sources.get("redirect_uri"),
            ),
        ),
        prerequisites=_items(guide, "prerequisite"),
        steps=_items(guide, "step"),
        blockers=_items(guide, "blocker"),
        human_actions=_items(guide, "human_action"),
        sources=[
            SourceModel(
                title=source.title,
                url=source.url,
                publisher=source.publisher,
                accessed_on=source.accessed_on,
            )
            for source in sorted(guide.sources, key=lambda source: source.position)
        ],
        pending_candidate=pending,
    )
