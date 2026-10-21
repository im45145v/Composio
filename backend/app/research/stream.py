"""Server-Sent Events for a research run. Reconnects resume from Last-Event-ID."""

from __future__ import annotations

import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import ResearchEvent, ResearchRun
from app.research.store import TERMINAL


def format_sse(event_id: int, event: str, data: dict) -> str:
    body = json.dumps(data, separators=(",", ":"), default=str)
    return f"id: {event_id}\nevent: {event}\ndata: {body}\n\n"


def stream_events(session_factory: sessionmaker[Session], run_id: str, after_id: int):
    seen = after_id
    started = time.monotonic()
    while time.monotonic() - started < 120:
        with session_factory() as session:
            run = session.get(ResearchRun, run_id)
            if run is None:
                yield format_sse(
                    0,
                    "terminal",
                    {
                        "stage": "failed",
                        "status": "failed",
                        "code": "not_found",
                        "message": "No research run exists for this address.",
                        "guide_created": False,
                    },
                )
                return
            rows = session.scalars(
                select(ResearchEvent)
                .where(ResearchEvent.run_id == run_id, ResearchEvent.id > seen)
                .order_by(ResearchEvent.id.asc())
            ).all()
            terminal = run.status in TERMINAL
            copied = [
                (row.id, row.stage, row.message, json.loads(row.payload_json) if row.payload_json else {})
                for row in rows
            ]
        for event_id, stage, message, payload in copied:
            kind = "terminal" if stage in TERMINAL else "finding" if payload.get("url") else "stage"
            yield format_sse(event_id, kind, {"stage": stage, "message": message, **payload})
            seen = event_id
        if terminal:
            return
        yield ": keep-alive\n\n"
        time.sleep(0.2)
    yield format_sse(
        seen,
        "stage",
        {"stage": "waiting", "message": "Still running. Reconnect to continue."},
    )
