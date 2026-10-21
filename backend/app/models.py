"""SQLite tables for guides and the claims inside them."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    auth_type_value: Mapped[str] = mapped_column(String(80))
    auth_type_status: Mapped[str] = mapped_column(String(20))
    auth_type_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    setup_path: Mapped[str] = mapped_column(String(40), index=True)
    setup_path_label: Mapped[str] = mapped_column(String(160))
    setup_path_status: Mapped[str] = mapped_column(String(20))
    setup_path_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty_value: Mapped[str] = mapped_column(String(80))
    difficulty_status: Mapped[str] = mapped_column(String(20))
    difficulty_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_effort_value: Mapped[str] = mapped_column(Text)
    active_effort_status: Mapped[str] = mapped_column(String(20))
    active_effort_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_wait_value: Mapped[str] = mapped_column(Text)
    approval_wait_status: Mapped[str] = mapped_column(String(20))
    approval_wait_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_value: Mapped[str] = mapped_column(String(40))
    confidence_status: Mapped[str] = mapped_column(String(20))
    confidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    managed_value: Mapped[str] = mapped_column(Text)
    managed_status: Mapped[str] = mapped_column(String(20))
    managed_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    byo_value: Mapped[str] = mapped_column(Text)
    byo_status: Mapped[str] = mapped_column(String(20))
    byo_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    redirect_value: Mapped[str] = mapped_column(Text)
    redirect_status: Mapped[str] = mapped_column(String(20))
    redirect_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(Text)
    execution_note: Mapped[str] = mapped_column(Text)
    tested: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[date] = mapped_column(Date)

    items: Mapped[list[GuideItem]] = relationship(
        back_populates="guide",
        cascade="all, delete-orphan",
        order_by="GuideItem.position",
    )
    sources: Mapped[list[Source]] = relationship(
        back_populates="guide",
        cascade="all, delete-orphan",
        order_by="Source.position",
    )


class GuideItem(Base):
    __tablename__ = "guide_items"
    __table_args__ = (UniqueConstraint("guide_id", "kind", "position", name="uq_item_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    guide: Mapped[Guide] = relationship(back_populates="items")


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("guide_id", "url", name="uq_source_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
    publisher: Mapped[str] = mapped_column(String(80))
    accessed_on: Mapped[date] = mapped_column(Date)

    guide: Mapped[Guide] = relationship(back_populates="sources")


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    app_name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(80), index=True)
    docs_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    stage: Mapped[str] = mapped_column(String(32))
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    guide_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    guide_created: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    events: Mapped[list[ResearchEvent]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ResearchEvent.id",
    )
    evidence: Mapped[list[EvidenceRecord]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvidenceRecord.id",
    )


class ActiveResearch(Base):
    """One in-flight run per app. The row is the duplicate lock."""

    __tablename__ = "active_research"

    normalized_name: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36))


class ResearchEvent(Base):
    __tablename__ = "research_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    run: Mapped[ResearchRun] = relationship(back_populates="events")


class EvidenceRecord(Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("run_id", "evidence_key", name="uq_evidence_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    evidence_key: Mapped[str] = mapped_column(String(16))
    url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(200))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    excerpt: Mapped[str] = mapped_column(Text)
    supports_json: Mapped[str] = mapped_column(Text, default="[]")

    run: Mapped[ResearchRun] = relationship(back_populates="evidence")
