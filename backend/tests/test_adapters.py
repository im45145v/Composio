"""Vendor adapters build real HTTP requests. The transport is mocked."""

from __future__ import annotations

import os

import httpx

from app.research.llm import AnthropicModel, OpenAIModel
from app.research.search import BraveSearch, TavilySearch


def test_tavily_retries_a_transient_failure_then_parses_hits():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url == "https://api.tavily.com/search"
        assert b"test-key" in request.content
        if calls["count"] == 1:
            return httpx.Response(503, json={"error": "busy"})
        return httpx.Response(
            200,
            json={"results": [{"title": "OAuth", "url": "https://docs.example/oauth", "content": "snippet"}]},
        )

    hits = TavilySearch("test-key", transport=httpx.MockTransport(handler)).search("example oauth", limit=3)
    assert calls["count"] == 2
    assert hits[0].url == "https://docs.example/oauth"
    assert hits[0].title == "OAuth"


def test_brave_parses_web_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Subscription-Token"] == "test-key"
        assert request.url.params["q"] == "example oauth"
        return httpx.Response(
            200,
            json={"web": {"results": [{"title": "Docs", "url": "https://docs.example/oauth", "description": "text"}]}},
        )

    hits = BraveSearch("test-key", transport=httpx.MockTransport(handler)).search("example oauth", limit=2)
    assert hits[0].title == "Docs"


def test_openai_adapter_requests_json_and_retries():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url == "https://api.openai.com/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        body = request.read().decode()
        assert "json_object" in body
        if calls["count"] == 1:
            return httpx.Response(503, json={"error": "busy"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "{\"ok\": true}"}}]})

    text = OpenAIModel("test-key", "gpt-4o-mini", transport=httpx.MockTransport(handler)).complete(
        system="system",
        user="user",
    )
    assert text == "{\"ok\": true}"
    assert calls["count"] == 2


def test_anthropic_adapter_reads_text_blocks():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        return httpx.Response(200, json={"content": [{"type": "text", "text": "{\"ok\": true}"}]})

    text = AnthropicModel("test-key", "claude-sonnet-4-5", transport=httpx.MockTransport(handler)).complete(
        system="system",
        user="user",
    )
    assert text == "{\"ok\": true}"


def test_env_file_fills_unset_keys_only(tmp_path, monkeypatch):
    from app.config import load_env_file

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "export MODEL_PROVIDER=anthropic",
                "MODEL_API_KEY=from-file",
                'SEARCH_API_KEY="from-file"',
                "",
            ]
        )
    )
    monkeypatch.setenv("MODEL_API_KEY", "from-env")
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    load_env_file(env_file)
    assert os.environ["MODEL_API_KEY"] == "from-env"
    assert os.environ["SEARCH_API_KEY"] == "from-file"
    assert os.environ["MODEL_PROVIDER"] == "anthropic"
    load_env_file(tmp_path / "missing.env")


def test_factory_selects_the_configured_vendors(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'guides.db'}")
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("SEARCH_PROVIDER", "brave")
    from app.main import create_app

    application = create_app()
    assert application.state.research.configured is True
    assert isinstance(application.state.research.model, AnthropicModel)
    assert isinstance(application.state.research.search, BraveSearch)

    monkeypatch.setenv("MODEL_PROVIDER", "nope")
    unconfigured = create_app()
    assert unconfigured.state.research.configured is False
