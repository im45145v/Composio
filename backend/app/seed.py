"""Load official-doc guides into SQLite. Re-running replaces guide text in place."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import create_db_engine
from app.models import Base, Guide, GuideItem, Source
from app.seed_data import GUIDES

CLAIM_STATUSES = {"verified", "documented", "uncertain", "inferred", "unknown"}
SETUP_PATHS = {"managed_or_own", "own_app_unless_confirmed"}
KIND_FIELDS = (
    ("prerequisite", "prerequisites"),
    ("step", "steps"),
    ("blocker", "blockers"),
    ("human_action", "human_actions"),
)
CLAIM_PREFIXES = (
    "auth_type",
    "difficulty",
    "active_effort",
    "approval_wait",
    "confidence",
    "managed",
    "byo",
    "redirect",
)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
    _ensure_columns(engine)


def _ensure_columns(engine) -> None:
    """Add columns that create_all does not apply to a database that already exists."""

    if engine.dialect.name != "sqlite":
        return
    additions = {
        "guides": (
            "claim_sources_json",
            "ALTER TABLE guides ADD COLUMN claim_sources_json TEXT NOT NULL DEFAULT '{}'",
        ),
        "guide_items": (
            "source_url",
            "ALTER TABLE guide_items ADD COLUMN source_url VARCHAR(500)",
        ),
    }
    with engine.begin() as connection:
        for table, (column, statement) in additions.items():
            rows = connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            names = {row[1] for row in rows}
            if names and column not in names:
                connection.exec_driver_sql(statement)


def seed_database(engine) -> None:
    from app.database import create_session_factory

    session_factory = create_session_factory(engine)
    with session_factory() as session:
        slugs = [payload["slug"] for payload in GUIDES]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Seed slugs must be unique.")
        for payload in GUIDES:
            _upsert_guide(session, payload)
        session.commit()


def _require_status(status: str, label: str) -> None:
    if status not in CLAIM_STATUSES:
        raise ValueError(f"{label} has unknown claim status {status!r}.")


def _upsert_guide(session: Session, payload: dict) -> None:
    slug = payload["slug"]
    guide = session.scalar(select(Guide).where(Guide.slug == slug))
    if guide is None:
        guide = Guide(slug=slug, name=payload["name"], summary=payload["summary"])
        session.add(guide)

    guide.name = payload["name"]
    guide.summary = payload["summary"]
    guide.decision = payload["decision"]
    guide.execution_note = payload["execution_note"]
    guide.tested = bool(payload["tested"])
    guide.last_checked = payload["last_checked"]
    guide.claim_sources_json = "{}"

    setup = payload["setup_path"]
    if setup["value"] not in SETUP_PATHS:
        raise ValueError(f"{slug} has unknown setup path {setup['value']!r}.")
    _require_status(setup["status"], f"{slug} setup path")
    guide.setup_path = setup["value"]
    guide.setup_path_label = setup["label"]
    guide.setup_path_status = setup["status"]
    guide.setup_path_note = setup.get("note")

    for prefix in CLAIM_PREFIXES:
        claim = payload[prefix]
        _require_status(claim["status"], f"{slug} {prefix}")
        setattr(guide, f"{prefix}_value", claim["value"])
        setattr(guide, f"{prefix}_status", claim["status"])
        setattr(guide, f"{prefix}_note", claim.get("note"))

    guide.items.clear()
    guide.sources.clear()
    session.flush()

    for kind, field in KIND_FIELDS:
        for position, item in enumerate(payload[field], start=1):
            _require_status(item["status"], f"{slug} {kind} {position}")
            guide.items.append(
                GuideItem(
                    kind=kind,
                    position=position,
                    title=item["title"],
                    body=item["body"],
                    status=item["status"],
                    note=item.get("note"),
                )
            )

    for position, source in enumerate(payload["sources"], start=1):
        url = source["url"]
        if not url.startswith("https://"):
            raise ValueError(f"{slug} source {url!r} must be an https URL.")
        guide.sources.append(
            Source(
                position=position,
                title=source["title"],
                url=url,
                publisher=source["publisher"],
                accessed_on=payload["last_checked"],
            )
        )


def main() -> None:
    from app.config import load_settings

    settings = load_settings()
    engine = create_db_engine(settings.database_url)
    init_db(engine)
    seed_database(engine)


if __name__ == "__main__":
    main()
