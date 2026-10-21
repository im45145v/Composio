"""Load official-doc guides into SQLite. Re-running replaces guide text in place."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import create_db_engine
from app.models import Base, Guide, GuideItem, Source
from app.seed_data import GUIDES

CLAIM_STATUSES = {"verified", "documented", "uncertain", "inferred", "unknown"}
SETUP_PATHS = {"managed_or_own", "own_app_unless_confirmed"}
AUDIENCES = {"managed", "own", "shared"}
# Items omitted here are shared: they belong on both the managed path and the own-app path.
ITEM_AUDIENCE: dict[tuple[str, str, str], str] = {
    ("github", "prerequisite", "A GitHub account that can own the app"): "own",
    ("github", "prerequisite", "A public homepage URL"): "own",
    ("github", "prerequisite", "The callback URL you will actually use"): "own",
    ("github", "step", "Decide that an OAuth app is the credential you are creating"): "own",
    ("github", "step", "Open the new OAuth app form"): "own",
    ("github", "step", "Enter the public application details"): "own",
    ("github", "step", "Set device flow and token expiration on purpose"): "own",
    ("github", "step", "Register the application"): "own",
    ("github", "step", "Keep the client ID and client secret"): "own",
    ("github", "step", "Send the user through GitHub's authorization screen"): "own",
    ("github", "blocker", "An OAuth app cannot act without a user"): "own",
    ("github", "blocker", "The 100-app ownership cap"): "own",
    ("github", "blocker", "Callback and Composio redirect must match"): "own",
    ("github", "blocker", "The authorization code expires after 10 minutes"): "own",
    ("github", "blocker", "Expiring user tokens are on by default"): "own",
    ("github", "blocker", "Organization restrictions are conditional"): "own",
    ("github", "blocker", "Managed auth shows Composio on the consent screen"): "managed",
    ("github", "blocker", "The shared app shares quota"): "managed",
    ("github", "human_action", "Someone with admin rights submits the form"): "own",
    ("github", "human_action", "Someone chooses the expiration checkbox"): "own",
    ("github", "human_action", "An organization owner may have to grant access"): "own",
    ("github", "human_action", "Someone copies the client secret into Composio"): "own",
    ("slack", "prerequisite", "A Slack workspace for development"): "own",
    ("slack", "prerequisite", "An HTTPS redirect that matches the auth config"): "own",
    ("slack", "step", "Create the app in a development workspace"): "own",
    ("slack", "step", "Install it on the owning workspace"): "own",
    ("slack", "step", "Configure the redirect under OAuth and Permissions"): "own",
    ("slack", "step", "Request bot scopes and user scopes separately"): "own",
    ("slack", "step", "Wait for a person to approve the scopes"): "own",
    ("slack", "step", "Exchange the code before it expires"): "own",
    ("slack", "step", "Activate public distribution only for other workspaces"): "own",
    ("slack", "step", "Submit to the Marketplace only if you want a listing"): "own",
    ("slack", "blocker", "An undistributed app cannot move workspaces"): "own",
    ("slack", "blocker", "Redirect mismatches fail the install"): "own",
    ("slack", "blocker", "The authorization code lasts ten minutes"): "own",
    ("slack", "blocker", "Published Marketplace apps can reject unapproved scopes"): "own",
    ("slack", "blocker", "Managed auth keeps Composio on the consent screen"): "managed",
    ("slack", "human_action", "A person creates the app and picks the workspace"): "own",
    ("slack", "human_action", "Someone finishes the distribution checklist"): "own",
    ("slack", "human_action", "Marketplace listing is a separate submission"): "own",
    ("slack", "human_action", "Existing workspaces reinstall after scope changes"): "own",
    ("slack", "human_action", "Someone enters the client credentials in Composio"): "own",
    ("google-calendar", "prerequisite", "Managed auth does not start with a Cloud project"): "managed",
    ("google-calendar", "prerequisite", "An own client needs a Google Cloud project"): "own",
    ("google-calendar", "prerequisite", "One redirect URI, shared by Google and Composio"): "own",
    ("google-calendar", "step", "Start with managed auth unless you need your own client"): "managed",
    ("google-calendar", "step", "Configure branding and audience on your own client"): "own",
    ("google-calendar", "step", "Add test users while an external app stays in Testing"): "own",
    ("google-calendar", "step", "Enable the Calendar API and create a web client"): "own",
    ("google-calendar", "step", "Resolve the client id and client secret before pasting them"): "own",
    ("google-calendar", "step", "Submit verification only when audience and scope class require it"): "own",
    ("google-calendar", "blocker", "The Google how-to and current docs name different callbacks"): "own",
    ("google-calendar", "blocker", "External Testing is a closed 100-user, seven-day list"): "own",
    ("google-calendar", "blocker", "Web client secret versus Composio's form"): "own",
    ("google-calendar", "blocker", "No single verification duration applies to Calendar"): "own",
    ("google-calendar", "human_action", "Someone creates the Cloud project only for an own client"): "own",
    ("google-calendar", "human_action", "Someone chooses Internal or External"): "own",
    ("google-calendar", "human_action", "Someone sets the AI-agent checkbox before Create"): "own",
    ("google-calendar", "human_action", "Someone maintains the test-user list"): "own",
    ("google-calendar", "human_action", "Verification, when it applies, is a human submission"): "own",
}
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
# Column prefixes and the public claim names the API reads from claim_sources_json.
CLAIM_SOURCE_KEYS = {
    "byo": "bring_your_own",
    "redirect": "redirect_uri",
}


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
    _ensure_columns(engine)


def _ensure_columns(engine) -> None:
    """Add columns that create_all does not apply to a database that already exists."""

    if engine.dialect.name != "sqlite":
        return
    additions = {
        "guides": (
            ("claim_sources_json", "ALTER TABLE guides ADD COLUMN claim_sources_json TEXT NOT NULL DEFAULT '{}'"),
            ("origin", "ALTER TABLE guides ADD COLUMN origin VARCHAR(20) NOT NULL DEFAULT 'editorial'"),
        ),
        "guide_items": (
            ("source_url", "ALTER TABLE guide_items ADD COLUMN source_url VARCHAR(500)"),
            ("audience", "ALTER TABLE guide_items ADD COLUMN audience VARCHAR(16) NOT NULL DEFAULT 'shared'"),
        ),
        "research_runs": (
            ("purpose", "ALTER TABLE research_runs ADD COLUMN purpose VARCHAR(16) NOT NULL DEFAULT 'create'"),
            ("target_slug", "ALTER TABLE research_runs ADD COLUMN target_slug VARCHAR(80)"),
        ),
    }
    with engine.begin() as connection:
        for table, columns in additions.items():
            rows = connection.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            names = {row[1] for row in rows}
            if not names:
                continue
            for column, statement in columns:
                if column not in names:
                    connection.exec_driver_sql(statement)


GENERATED = Path(__file__).resolve().parent / "generated"


def seed_database(engine) -> None:
    from app.database import create_session_factory

    session_factory = create_session_factory(engine)
    with session_factory() as session:
        payloads = [*GUIDES, *_generated_payloads()]
        slugs = [payload["slug"] for payload in payloads]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Seed slugs must be unique.")
        for payload in payloads:
            _upsert_guide(session, payload)
        session.commit()


def _generated_payloads() -> list[dict]:
    if not GENERATED.is_dir():
        return []
    payloads = []
    for path in sorted(GENERATED.glob("*.json")):
        detail = json.loads(path.read_text())
        payloads.append(_payload_from_detail(detail))
    return payloads


def _payload_from_detail(detail: dict) -> dict:
    checked = detail["last_checked"]
    if isinstance(checked, str):
        checked = date.fromisoformat(checked)
    composio = detail["composio"]
    origin = detail.get("origin")
    if origin not in {"editorial", "researched"}:
        origin = "researched"
    return {
        "slug": detail["slug"],
        "name": detail["name"],
        "summary": detail["summary"],
        "decision": detail["decision"],
        "execution_note": detail["execution_note"],
        "tested": bool(detail["tested"]),
        "last_checked": checked,
        "origin": origin,
        "managed_by_seed": True,
        "auth_type": detail["auth_type"],
        "setup_path": detail["setup_path"],
        "difficulty": detail["difficulty"],
        "active_effort": detail["active_effort"],
        "approval_wait": detail["approval_wait"],
        "confidence": detail["confidence"],
        "managed": composio["managed"],
        "byo": composio["bring_your_own"],
        "redirect": composio["redirect_uri"],
        "prerequisites": detail["prerequisites"],
        "steps": detail["steps"],
        "blockers": detail["blockers"],
        "human_actions": detail["human_actions"],
        "sources": detail["sources"],
    }


def _require_status(status: str, label: str) -> None:
    if status not in CLAIM_STATUSES:
        raise ValueError(f"{label} has unknown claim status {status!r}.")


def _upsert_guide(session: Session, payload: dict) -> None:
    slug = payload["slug"]
    guide = session.scalar(select(Guide).where(Guide.slug == slug))
    if guide is not None and guide.origin == "researched" and not payload.get("managed_by_seed"):
        return
    if guide is None:
        guide = Guide(slug=slug, name=payload["name"], summary=payload["summary"], origin="editorial")
        session.add(guide)
    guide.origin = payload.get("origin", "editorial")

    guide.name = payload["name"]
    guide.summary = payload["summary"]
    guide.decision = payload["decision"]
    guide.execution_note = payload["execution_note"]
    guide.tested = bool(payload["tested"])
    guide.last_checked = payload["last_checked"]
    claim_sources: dict[str, str] = {}

    setup = payload["setup_path"]
    if setup["value"] not in SETUP_PATHS:
        raise ValueError(f"{slug} has unknown setup path {setup['value']!r}.")
    _require_status(setup["status"], f"{slug} setup path")
    guide.setup_path = setup["value"]
    guide.setup_path_label = setup["label"]
    guide.setup_path_status = setup["status"]
    guide.setup_path_note = setup.get("note")

    if setup.get("source_url"):
        claim_sources["setup_path"] = setup["source_url"]

    for prefix in CLAIM_PREFIXES:
        claim = payload[prefix]
        _require_status(claim["status"], f"{slug} {prefix}")
        setattr(guide, f"{prefix}_value", claim.get("value") or "Unknown")
        setattr(guide, f"{prefix}_status", claim["status"])
        setattr(guide, f"{prefix}_note", claim.get("note"))
        if claim.get("source_url"):
            claim_sources[CLAIM_SOURCE_KEYS.get(prefix, prefix)] = claim["source_url"]
    guide.claim_sources_json = json.dumps(claim_sources)

    guide.items.clear()
    guide.sources.clear()
    session.flush()

    for kind, field in KIND_FIELDS:
        for position, item in enumerate(payload[field], start=1):
            _require_status(item["status"], f"{slug} {kind} {position}")
            supplied = item.get("audience")
            audience = supplied if supplied in AUDIENCES else ITEM_AUDIENCE.get((slug, kind, item["title"]), "shared")
            if audience not in AUDIENCES:
                raise ValueError(f"{slug} {kind} {item['title']!r} has unknown audience {audience!r}.")
            guide.items.append(
                GuideItem(
                    kind=kind,
                    position=position,
                    title=item["title"],
                    body=item["body"],
                    status=item["status"],
                    note=item.get("note"),
                    source_url=item.get("source_url"),
                    audience=audience,
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
