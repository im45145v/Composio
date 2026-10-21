"""API contracts. Claim status is part of every factual field."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

ClaimStatus = Literal["verified", "documented", "uncertain", "inferred", "unknown"]
SetupPathValue = Literal["managed_or_own", "own_app_unless_confirmed"]
ItemKind = Literal["prerequisite", "step", "blocker", "human_action"]


class ClaimModel(BaseModel):
    value: str | None = None
    status: ClaimStatus
    note: str | None = None
    source_url: str | None = None


class SetupPathModel(BaseModel):
    value: SetupPathValue
    label: str
    status: ClaimStatus
    note: str | None = None
    source_url: str | None = None


class GuideItemModel(BaseModel):
    position: int
    title: str
    body: str
    status: ClaimStatus
    note: str | None = None
    source_url: str | None = None


class SourceModel(BaseModel):
    title: str
    url: str
    publisher: str
    accessed_on: date


class ComposioSection(BaseModel):
    decision: str
    managed: ClaimModel
    bring_your_own: ClaimModel
    redirect_uri: ClaimModel


class GuideSummary(BaseModel):
    slug: str
    name: str
    summary: str
    auth_type: ClaimModel
    setup_path: SetupPathModel
    difficulty: ClaimModel
    active_effort: ClaimModel
    approval_wait: ClaimModel
    confidence: ClaimModel
    tested: bool
    last_checked: date


class GuideDetail(GuideSummary):
    execution_note: str
    composio: ComposioSection
    prerequisites: list[GuideItemModel]
    steps: list[GuideItemModel]
    blockers: list[GuideItemModel]
    human_actions: list[GuideItemModel]
    sources: list[SourceModel]


class GuideListResponse(BaseModel):
    guides: list[GuideSummary]
    count: int


class ResearchRequest(BaseModel):
    app_name: str = Field(min_length=1, max_length=120)
    docs_url: HttpUrl | None = None

    @field_validator("app_name")
    @classmethod
    def require_visible_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Enter the app name.")
        return cleaned


class ResearchUnavailable(BaseModel):
    code: Literal["research_unavailable"]
    message: str
    app_name: str
    docs_url: str | None
    guide_created: Literal[False]


class GuideExistsResponse(BaseModel):
    code: Literal["guide_exists"]
    app_name: str
    slug: str
    guide_url: str
    guide_created: Literal[False]


class ResearchAccepted(BaseModel):
    code: Literal["research_started", "research_in_progress"]
    run_id: str
    app_name: str
    events_url: str
    status: str
    guide_created: bool
    guide_url: str | None = None
    slug: str | None = None


class EvidenceView(BaseModel):
    evidence_key: str
    url: str
    title: str
    retrieved_at: str
    supports: list[str]


class ResearchRunView(BaseModel):
    id: str
    app_name: str
    status: str
    stage: str
    error_code: str | None
    message: str | None
    guide_slug: str | None
    guide_url: str | None
    guide_created: bool
    evidence: list[EvidenceView]
