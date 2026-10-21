"""Wire the configured search and model adapters. Missing keys leave research off."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.research.llm import AnthropicModel, BackboardModel, GemmaModel, ModelClient, OpenAIModel
from app.research.reader import PageReader
from app.research.search import BraveSearch, SearchClient, TavilySearch

OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
# Guide extraction needs schema adherence inside the research deadline. gpt-4.1 does that without a reasoning pass.
BACKBOARD_OPENAI_DEFAULT_MODEL = "gpt-4.1"
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-5"
GEMMA_DEFAULT_MODEL = "gemma-4-26b-a4b-it"
MODEL_PROVIDERS = {"openai", "anthropic", "backboard", "gemma"}


@dataclass(frozen=True)
class ResearchDeps:
    configured: bool
    inline: bool
    search: SearchClient | None
    model: ModelClient | None
    reader: PageReader
    max_pages: int
    max_results: int
    deadline_seconds: float
    unavailable_reason: str | None = None


def build_research(settings: Settings) -> ResearchDeps:
    reader = PageReader(timeout=settings.page_timeout_seconds, max_bytes=settings.page_max_bytes)
    reason = _unavailable_reason(settings)
    if reason is not None:
        return ResearchDeps(
            configured=False,
            inline=settings.research_inline,
            search=None,
            model=None,
            reader=reader,
            max_pages=settings.max_research_pages,
            max_results=settings.max_search_results,
            deadline_seconds=settings.research_deadline_seconds,
            unavailable_reason=reason,
        )
    model_name = settings.model_name or _default_model(settings)
    model = _build_model(settings, model_name)
    search: SearchClient
    if settings.search_provider == "brave":
        search = BraveSearch(settings.search_api_key or "", timeout=settings.search_timeout_seconds)
    else:
        search = TavilySearch(settings.search_api_key or "", timeout=settings.search_timeout_seconds)
    return ResearchDeps(
        configured=True,
        inline=settings.research_inline,
        search=search,
        model=model,
        reader=reader,
        max_pages=settings.max_research_pages,
        max_results=settings.max_search_results,
        deadline_seconds=settings.research_deadline_seconds,
        unavailable_reason=None,
    )


def _default_model(settings: Settings) -> str:
    if settings.model_provider == "anthropic":
        return ANTHROPIC_DEFAULT_MODEL
    if settings.model_provider == "gemma":
        return GEMMA_DEFAULT_MODEL
    if settings.model_provider == "backboard":
        if settings.backboard_llm_provider == "google":
            return GEMMA_DEFAULT_MODEL
        return BACKBOARD_OPENAI_DEFAULT_MODEL
    return OPENAI_DEFAULT_MODEL


def _build_model(settings: Settings, model_name: str) -> ModelClient:
    key = settings.model_api_key or ""
    timeout = settings.model_timeout_seconds
    if settings.model_provider == "anthropic":
        return AnthropicModel(key, model_name, timeout=timeout)
    if settings.model_provider == "gemma":
        return GemmaModel(key, model_name, timeout=timeout)
    if settings.model_provider == "backboard":
        return BackboardModel(
            key,
            model_name,
            llm_provider=settings.backboard_llm_provider,
            timeout=timeout,
        )
    return OpenAIModel(key, model_name, timeout=timeout)


def _unavailable_reason(settings: Settings) -> str | None:
    if settings.model_provider not in MODEL_PROVIDERS:
        return "The model provider is not recognized. Use openai, anthropic, backboard, or gemma."
    if settings.search_provider not in {"tavily", "brave"}:
        return "The search provider is not recognized. Use tavily or brave."
    if not settings.model_api_key or not settings.search_api_key:
        return (
            "Live research is not configured. No model provider is connected until "
            "MODEL_API_KEY and SEARCH_API_KEY are set, and this request did not create a guide."
        )
    return None
