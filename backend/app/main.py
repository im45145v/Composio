"""Application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_settings
from app.database import bind_database
from app.research.runtime import build_research
from app.routers import guides, research
from app.seed import init_db, seed_database


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(
        title="Field Guide API",
        summary="Searchable OAuth setup guides. Research runs when a model and search provider are configured.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Last-Event-ID"],
    )
    engine = bind_database(app, settings)
    app.state.research = build_research(settings)
    init_db(engine)
    from app.research.store import abandon_interrupted_runs

    abandon_interrupted_runs(app.state.session_factory)
    if settings.seed_on_startup:
        seed_database(engine)

    app.include_router(guides.router, prefix="/api")
    app.include_router(research.router, prefix="/api")

    @app.get("/api/health")
    def health(request: Request) -> dict[str, str]:
        configured = bool(request.app.state.research.configured)
        return {"status": "ok", "research": "configured" if configured else "unavailable"}

    return app


app = create_app()
