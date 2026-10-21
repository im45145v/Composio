"""Turn a name or website into a stable app identity and an existing guide, if one exists."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Guide
from app.research.errors import InvalidAppName
from app.research.safety import screen_url

KNOWN = {
    "github": "github",
    "google-calendar": "google-calendar",
    "google calendar": "google-calendar",
    "gcal": "google-calendar",
    "slack": "slack",
}
HOSTS = {
    "github.com": "github",
    "www.github.com": "github",
    "docs.github.com": "github",
    "api.github.com": "github",
    "slack.com": "slack",
    "www.slack.com": "slack",
    "api.slack.com": "slack",
    "docs.slack.dev": "slack",
    "calendar.google.com": "google-calendar",
}
DISPLAY = {
    "github": "GitHub",
    "slack": "Slack",
    "google-calendar": "Google Calendar",
}
GENERIC_LABELS = {"www", "docs", "developer", "developers", "api", "app", "www2"}


@dataclass(frozen=True)
class Identity:
    app_name: str
    normalized_name: str
    docs_url: str | None
    matched_slug: str | None


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")[:80]


def _looks_like_url(value: str) -> bool:
    if value.startswith(("http://", "https://")):
        return True
    return " " not in value and "." in value


def _label_from_host(host: str) -> str:
    matched = HOSTS.get(host)
    if matched:
        return DISPLAY[matched]
    labels = [part for part in host.split(".") if part not in GENERIC_LABELS]
    core = labels[-2] if len(labels) >= 2 else (labels[0] if labels else host)
    return core.replace("-", " ").title()


def interpret(app_name: str, docs_url: str | None) -> Identity:
    cleaned = " ".join(app_name.split())
    if not cleaned:
        raise InvalidAppName("Enter the app name.")
    supplied = screen_url(docs_url) if docs_url else None
    matched: str | None = None
    if _looks_like_url(cleaned):
        raw = cleaned if "://" in cleaned else f"https://{cleaned}"
        website = screen_url(raw)
        host = urlsplit(website).hostname or ""
        display = _label_from_host(host)
        docs = supplied or website
        matched = HOSTS.get(host)
    else:
        display = cleaned
        docs = supplied
        matched = KNOWN.get(display.casefold()) or KNOWN.get(slugify(display))
    slug = matched or slugify(display)
    if not slug:
        raise InvalidAppName("Enter an app name or a public website.")
    return Identity(
        app_name=display[:120],
        normalized_name=slug,
        docs_url=docs,
        matched_slug=matched,
    )


def find_existing(session: Session, identity: Identity) -> Guide | None:
    slug = identity.matched_slug or identity.normalized_name
    guide = session.scalar(select(Guide).where(Guide.slug == slug))
    if guide is not None:
        return guide
    return session.scalar(select(Guide).where(func.lower(Guide.name) == identity.app_name.casefold()))
