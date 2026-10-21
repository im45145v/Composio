"""Application factory."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import load_settings
from app.database import bind_database
from app.research.runtime import build_research
from app.routers import guides, research
from app.seed import init_db, seed_database


def _frontend_dist() -> Path | None:
    override = os.environ.get("STATIC_DIR", "").strip()
    dist = Path(override).resolve() if override else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    return dist if (dist / "index.html").is_file() else None


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built SPA, including direct loads of /guides/* and /research."""

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")
    index = dist / "index.html"

    def page(full_path: str) -> FileResponse:
        if full_path:
            candidate = (dist / full_path).resolve()
            try:
                candidate.relative_to(dist)
            except ValueError:
                return FileResponse(index)
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(index)

    @app.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return page("")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_page(full_path: str) -> FileResponse:
        return page(full_path)


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

    dist = _frontend_dist()
    if dist is not None:
        _mount_frontend(app, dist)

    return app


app = create_app()
