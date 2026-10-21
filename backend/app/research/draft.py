"""Structured guide the model must return. Memory is not a field."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DraftStatus = Literal["documented", "inferred", "unknown"]


class DraftClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: str | None = None
    status: DraftStatus
    note: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class DraftItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=12, max_length=2000)
    status: DraftStatus
    note: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class DraftConflict(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topic: str = Field(min_length=3, max_length=120)
    summary: str = Field(min_length=3, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list)


class DraftGuide(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(min_length=12, max_length=2000)
    decision: str = Field(min_length=12, max_length=2000)
    auth_type: DraftClaim
    setup_path_value: Literal["managed_or_own", "own_app_unless_confirmed"]
    setup_path_label: str = Field(min_length=3, max_length=160)
    setup_path_status: DraftStatus
    setup_path_note: str | None = None
    setup_path_evidence_ids: list[str] = Field(default_factory=list)
    difficulty: DraftClaim
    active_effort: DraftClaim
    approval_wait: DraftClaim
    confidence: DraftClaim
    managed: DraftClaim
    bring_your_own: DraftClaim
    redirect_uri: DraftClaim
    prerequisites: list[DraftItem] = Field(default_factory=list, max_length=8)
    steps: list[DraftItem] = Field(min_length=1, max_length=12)
    blockers: list[DraftItem] = Field(default_factory=list, max_length=8)
    human_actions: list[DraftItem] = Field(default_factory=list, max_length=8)
    conflicts: list[DraftConflict] = Field(default_factory=list, max_length=8)
