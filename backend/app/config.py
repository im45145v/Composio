"""Runtime settings. API keys stay on the backend and are never written into guides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _optional(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes"}


def _number(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]
    seed_on_startup: bool
    model_provider: str
    model_api_key: str | None
    model_name: str
    search_provider: str
    search_api_key: str | None
    research_inline: bool
    page_timeout_seconds: float
    page_max_bytes: int
    max_research_pages: int
    max_search_results: int
    model_timeout_seconds: float
    search_timeout_seconds: float
    research_deadline_seconds: float


def resolve_database_url(url: str) -> str:
    prefix = "sqlite:///"
    if not url.startswith(prefix) or url.startswith("sqlite:////"):
        return url
    raw_path = url[len(prefix) :]
    if raw_path.startswith("/") and not raw_path.startswith("./"):
        return url
    path = (BACKEND_ROOT / raw_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def load_env_file(path: Path) -> None:
    """Fill unset variables from a local env file. Existing variables win."""

    if not path.is_file():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[key] = value


def load_settings() -> Settings:
    load_env_file(BACKEND_ROOT / ".env")
    raw_origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = tuple(part.strip() for part in raw_origins.split(",") if part.strip())
    return Settings(
        database_url=resolve_database_url(
            os.environ.get("DATABASE_URL", "sqlite:///./data/guides.db")
        ),
        cors_origins=origins,
        seed_on_startup=_flag("SEED_ON_STARTUP", "true"),
        model_provider=os.environ.get("MODEL_PROVIDER", "openai").strip().lower() or "openai",
        model_api_key=_optional("MODEL_API_KEY"),
        model_name=os.environ.get("MODEL_NAME", "").strip(),
        search_provider=os.environ.get("SEARCH_PROVIDER", "tavily").strip().lower() or "tavily",
        search_api_key=_optional("SEARCH_API_KEY"),
        research_inline=_flag("RESEARCH_INLINE", "false"),
        page_timeout_seconds=_number("PAGE_TIMEOUT_SECONDS", 10),
        page_max_bytes=int(_number("PAGE_MAX_BYTES", 500_000)),
        max_research_pages=int(_number("MAX_RESEARCH_PAGES", 4)),
        max_search_results=int(_number("MAX_SEARCH_RESULTS", 5)),
        model_timeout_seconds=_number("MODEL_TIMEOUT_SECONDS", 45),
        search_timeout_seconds=_number("SEARCH_TIMEOUT_SECONDS", 10),
        research_deadline_seconds=_number("RESEARCH_DEADLINE_SECONDS", 90),
    )
