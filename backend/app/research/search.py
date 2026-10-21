"""Search adapters. Snippets are ranking hints only and are not model evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.research.errors import SearchError, TransientFailure, retry


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str = ""


class SearchClient(Protocol):
    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        """Return ranked hits. Implementations must not include the API key in errors."""


def _status_error(status: int, provider: str) -> SearchError:
    if status in {401, 403}:
        return SearchError(
            f"The {provider} search provider rejected the API key. Check SEARCH_API_KEY.",
            "search_failed",
        )
    if status in {429, 500, 502, 503, 504}:
        return TransientFailure(f"The {provider} search provider did not respond.", "search_failed")
    return SearchError(f"The {provider} search provider rejected the query.", "search_failed")


def _hits_from(items: list, *, url_key: str, title_key: str, snippet_key: str) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get(url_key)
        if not isinstance(url, str) or not url:
            continue
        title = item.get(title_key)
        snippet = item.get(snippet_key)
        hits.append(
            SearchHit(
                title=str(title or url)[:200],
                url=url,
                snippet=str(snippet or "")[:500],
            )
        )
    return hits


class TavilySearch:
    def __init__(self, api_key: str, *, timeout: float = 10, transport: httpx.BaseTransport | None = None) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._transport = transport

    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        def once() -> list[SearchHit]:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self._api_key,
                            "query": query,
                            "max_results": limit,
                            "include_answer": False,
                            "search_depth": "basic",
                        },
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The search provider timed out.", "search_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The search provider could not be reached.", "search_failed") from exc
            if response.status_code >= 400:
                raise _status_error(response.status_code, "Tavily")
            try:
                results = response.json().get("results", [])
            except ValueError as exc:
                raise SearchError("The search provider returned an unreadable response.", "search_failed") from exc
            if not isinstance(results, list):
                raise SearchError("The search provider returned an unreadable response.", "search_failed")
            return _hits_from(results, url_key="url", title_key="title", snippet_key="content")

        return retry(once)


class BraveSearch:
    def __init__(self, api_key: str, *, timeout: float = 10, transport: httpx.BaseTransport | None = None) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._transport = transport

    def search(self, query: str, *, limit: int) -> list[SearchHit]:
        def once() -> list[SearchHit]:
            try:
                with httpx.Client(timeout=self._timeout, transport=self._transport, trust_env=False) as client:
                    response = client.get(
                        "https://api.search.brave.com/res/v1/web/search",
                        params={"q": query, "count": str(limit)},
                        headers={"X-Subscription-Token": self._api_key, "Accept": "application/json"},
                    )
            except httpx.TimeoutException as exc:
                raise TransientFailure("The search provider timed out.", "search_failed") from exc
            except httpx.TransportError as exc:
                raise TransientFailure("The search provider could not be reached.", "search_failed") from exc
            if response.status_code >= 400:
                raise _status_error(response.status_code, "Brave")
            try:
                results = response.json().get("web", {}).get("results", [])
            except (ValueError, AttributeError) as exc:
                raise SearchError("The search provider returned an unreadable response.", "search_failed") from exc
            if not isinstance(results, list):
                raise SearchError("The search provider returned an unreadable response.", "search_failed")
            return _hits_from(results, url_key="url", title_key="title", snippet_key="description")

        return retry(once)
