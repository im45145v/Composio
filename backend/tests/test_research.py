"""Research runs against fake search, page, and model adapters. No paid APIs."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.research.errors import ModelError, SearchError, TransientFailure
from app.research.reader import FetchedPage
from app.research.search import SearchHit

EXAMPLE_DOCS = "https://docs.example.com/oauth"
COMPOSIO_DOCS = "https://docs.composio.dev/toolkits/example"
EXAMPLE_TEXT = (
    "Example uses OAuth 2.0. Create an OAuth app in the developer settings. "
    "The end user must approve the requested scopes."
)
COMPOSIO_TEXT = (
    "Composio-managed OAuth is available for Example. "
    "You do not need to register an OAuth app to use managed auth. "
    "Bring your own client for branding or custom scopes. "
    "Register the redirect URI https://backend.composio.dev/api/v3/toolkits/auth/callback."
)


def _claim(value, status, evidence, note=None):
    return {"value": value, "status": status, "note": note, "evidence_ids": evidence}


def valid_draft() -> dict:
    return {
        "summary": "Example uses OAuth 2.0 and can use Composio managed auth or a developer-owned client.",
        "decision": "Use managed auth when Composio's app is enough. Bring your own client for branding or custom scopes.",
        "auth_type": _claim("Example uses OAuth 2.0.", "documented", ["e1"]),
        "setup_path_value": "managed_or_own",
        "setup_path_label": "Managed auth or your own app",
        "setup_path_status": "documented",
        "setup_path_note": None,
        "setup_path_evidence_ids": ["e2"],
        "difficulty": _claim(None, "unknown", []),
        "active_effort": _claim(None, "unknown", []),
        "approval_wait": _claim(None, "unknown", []),
        "confidence": _claim(None, "unknown", []),
        "managed": _claim("Composio-managed OAuth is available for Example.", "documented", ["e2"]),
        "bring_your_own": _claim(
            "Bring your own client for branding or custom scopes.",
            "documented",
            ["e2"],
        ),
        "redirect_uri": _claim(
            "https://backend.composio.dev/api/v3/toolkits/auth/callback",
            "documented",
            ["e2"],
        ),
        "prerequisites": [
            {
                "title": "Developer settings",
                "body": "Create an OAuth app in the developer settings.",
                "status": "documented",
                "note": None,
                "evidence_ids": ["e1"],
            }
        ],
        "steps": [
            {
                "title": "Create the OAuth app",
                "body": "Create an OAuth app in the developer settings.",
                "status": "documented",
                "note": None,
                "evidence_ids": ["e1"],
            },
            {
                "title": "User approval",
                "body": "The end user must approve the requested scopes.",
                "status": "documented",
                "note": None,
                "evidence_ids": ["e1"],
            },
        ],
        "blockers": [],
        "human_actions": [
            {
                "title": "The end user approves access",
                "body": "The end user must approve the requested scopes.",
                "status": "documented",
                "note": None,
                "evidence_ids": ["e1"],
            }
        ],
        "conflicts": [],
    }


class FakeSearch:
    def __init__(self, hits=None, error: Exception | None = None) -> None:
        self.hits = hits if hits is not None else [
            SearchHit("Example OAuth", EXAMPLE_DOCS),
            SearchHit("Example toolkit", COMPOSIO_DOCS),
        ]
        self.error = error
        self.queries: list[str] = []

    def search(self, query: str, *, limit: int):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.hits[:limit]


class FakeReader:
    def __init__(self, pages: dict[str, tuple[str, str]]) -> None:
        self.pages = pages
        self.urls: list[str] = []

    def read(self, url: str) -> FetchedPage:
        self.urls.append(url)
        title, text = self.pages[url]
        return FetchedPage(url=url, title=title, text=text, retrieved_at=datetime.now(timezone.utc))


class FakeModel:
    def __init__(self, payload, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error
        self.systems: list[str] = []
        self.users: list[str] = []

    def complete(self, *, system: str, user: str) -> str:
        self.systems.append(system)
        self.users.append(user)
        if self.error:
            raise self.error
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload)


def _statuses(value, found: list[str]) -> None:
    if isinstance(value, dict):
        if "status" in value and isinstance(value["status"], str):
            found.append(value["status"])
        for child in value.values():
            _statuses(child, found)
    elif isinstance(value, list):
        for child in value:
            _statuses(child, found)


def read_events(client: TestClient, run_id: str, after: int | None = None) -> list[dict]:
    headers = {"Last-Event-ID": str(after)} if after is not None else None
    with client.stream("GET", f"/api/research-runs/{run_id}/events", headers=headers) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        raw = "".join(response.iter_text())
    events = []
    for block in raw.split("\n\n"):
        if not block.strip() or block.lstrip().startswith(":"):
            continue
        lines = [line for line in block.split("\n") if line]
        event_name = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
        data = next(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
        event_id = next(int(line.removeprefix("id: ")) for line in lines if line.startswith("id: "))
        events.append({"id": event_id, "event": event_name, "data": json.loads(data)})
    return events


@pytest.fixture
def research_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'guides.db'}")
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    monkeypatch.setenv("RESEARCH_INLINE", "true")
    from app.main import create_app

    application = create_app()
    search = FakeSearch()
    reader = FakeReader(
        {
            EXAMPLE_DOCS: ("Example OAuth", EXAMPLE_TEXT),
            COMPOSIO_DOCS: ("Example toolkit", COMPOSIO_TEXT),
        }
    )
    model = FakeModel(valid_draft())
    application.state.research = replace(
        application.state.research,
        configured=True,
        inline=True,
        search=search,
        model=model,
        reader=reader,
        unavailable_reason=None,
    )
    application.state.fakes = {"search": search, "reader": reader, "model": model}
    return application


def test_successful_run_persists_a_shareable_guide(research_app):
    with TestClient(research_app) as client:
        assert client.get("/api/health").json()["research"] == "configured"
        response = client.post(
            "/api/research-requests",
            json={"app_name": "Example", "docs_url": EXAMPLE_DOCS},
        )
        assert response.status_code == 202
        body = response.json()
        assert body["guide_created"] is True
        assert body["guide_url"] == "/guides/example"
        guide = client.get("/api/guides/example")
        assert guide.status_code == 200
        payload = guide.json()
        assert payload["tested"] is False
        assert payload["auth_type"]["value"] == "Example uses OAuth 2.0."
        assert payload["auth_type"]["status"] == "documented"
        assert payload["approval_wait"]["value"] is None
        assert payload["approval_wait"]["status"] == "unknown"
        assert payload["active_effort"]["status"] == "unknown"
        assert payload["composio"]["redirect_uri"]["value"].startswith("https://backend.composio.dev/")
        assert payload["auth_type"]["source_url"] == EXAMPLE_DOCS
        assert payload["steps"][0]["source_url"] == EXAMPLE_DOCS
        assert payload["human_actions"][0]["source_url"] == EXAMPLE_DOCS
        assert payload["composio"]["redirect_uri"]["source_url"] == COMPOSIO_DOCS
        assert payload["approval_wait"]["source_url"] is None
        statuses: list[str] = []
        _statuses(payload, statuses)
        assert "verified" not in statuses
        urls = [source["url"] for source in payload["sources"]]
        assert EXAMPLE_DOCS in urls
        assert COMPOSIO_DOCS in urls
        names = [item["name"] for item in client.get("/api/guides").json()["guides"]]
        assert "Example" in names
        run = client.get(f"/api/research-runs/{body['run_id']}").json()
        assert run["status"] == "completed"
        assert run["evidence"]
        assert run["evidence"][0]["retrieved_at"]
        assert any(item["supports"] for item in run["evidence"])
        prompt = research_app.state.fakes["model"].users[0]
        assert "Example uses OAuth 2.0." in prompt
        assert "untrusted data" in prompt
        assert "prior knowledge" in research_app.state.fakes["model"].systems[0].lower()
        events = read_events(client, body["run_id"])
        stages = [event["data"]["stage"] for event in events]
        assert "searching" in stages
        assert "reading" in stages
        assert any(event["event"] == "finding" for event in events)
        assert events[-1]["event"] == "terminal"
        assert events[-1]["data"]["status"] == "completed"
        replay = read_events(client, body["run_id"], after=events[0]["id"])
        assert events[0]["id"] not in [event["id"] for event in replay]
        assert replay[-1]["data"]["status"] == "completed"


def test_existing_guide_is_not_replaced(research_app):
    with TestClient(research_app) as client:
        before = client.get("/api/guides/github").json()
        response = client.post("/api/research-requests", json={"app_name": "GitHub"})
        assert response.status_code == 200
        assert response.json()["code"] == "guide_exists"
        assert response.json()["guide_url"] == "/guides/github"
        assert client.get("/api/guides/github").json()["summary"] == before["summary"]
        assert research_app.state.fakes["model"].systems == []
        created = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert created.status_code == 202
        research_app.state.fakes["model"].payload = valid_draft() | {
            "summary": "This replacement must not be stored."
        }
        again = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert again.status_code == 200
        assert again.json()["code"] == "guide_exists"
        assert "replacement" not in client.get("/api/guides/example").json()["summary"]


def test_invalid_input_and_ssrf_urls_are_rejected(client, research_app):
    with TestClient(research_app) as configured:
        for docs_url in (
            "http://127.0.0.1/secret",
            "http://169.254.169.254/latest/meta-data",
            "http://10.0.0.8/",
            "http://localhost/admin",
        ):
            response = configured.post(
                "/api/research-requests",
                json={"app_name": "Example", "docs_url": docs_url},
            )
            assert response.status_code == 422
            assert response.json()["detail"]["code"] in {"unsafe_url", "blocked_address", "unsupported_protocol"}
        name_url = configured.post("/api/research-requests", json={"app_name": "http://127.0.0.1/latest"})
        assert name_url.status_code == 422
        assert configured.get("/api/guides").json()["count"] == 32
    blank = client.post("/api/research-requests", json={"app_name": "   "})
    assert blank.status_code == 422
    private = client.post(
        "/api/research-requests",
        json={"app_name": "Notion", "docs_url": "http://192.168.1.20/docs"},
    )
    assert private.status_code == 422
    assert client.get("/api/guides/notion").json()["origin"] == "researched"


def test_search_failure_streams_a_terminal_error(research_app):
    research_app.state.fakes["search"].error = SearchError("down", "search_failed")
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        assert response.json()["guide_created"] is False
        events = read_events(client, response.json()["run_id"])
        assert any(event["data"]["stage"] == "searching" for event in events)
        assert events[-1]["event"] == "terminal"
        assert events[-1]["data"]["status"] == "failed"
        assert events[-1]["data"]["code"] == "search_failed"
        assert client.get("/api/guides/example").status_code == 404
        assert research_app.state.fakes["model"].systems == []


def test_model_failure_does_not_save_a_guide(research_app):
    research_app.state.fakes["model"].error = ModelError("down", "model_failed")
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "failed"
        assert run["error_code"] == "model_failed"
        assert client.get("/api/guides/example").status_code == 404


def test_missing_evidence_does_not_fabricate_a_guide(research_app):
    research_app.state.fakes["search"].hits = []
    reader = research_app.state.fakes["reader"]
    original_pages = dict(reader.pages)
    off_topic = "https://docs.other.test/oauth"
    reader.pages = {off_topic: ("Other product", "This page does not name the submitted app.")}
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": off_topic})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert client.get("/api/guides/example").status_code == 404
        assert research_app.state.fakes["model"].systems == []

    reader.pages = original_pages
    research_app.state.fakes["search"].hits = [
        SearchHit("Example OAuth", EXAMPLE_DOCS),
        SearchHit("Example toolkit", COMPOSIO_DOCS),
    ]
    draft = valid_draft()
    draft["auth_type"]["evidence_ids"] = []
    draft["steps"][0]["evidence_ids"] = []
    draft["steps"][1]["evidence_ids"] = []
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert "authentication type" in run["message"]
        assert client.get("/api/guides/example").status_code == 404


def test_conflicting_approval_waits_are_not_collapsed(research_app):
    research_app.state.fakes["reader"].pages = {
        EXAMPLE_DOCS: (
            "Example OAuth",
            EXAMPLE_TEXT + " Sensitive-scope verification typically takes 3-5 business days.",
        ),
        COMPOSIO_DOCS: (
            "Example toolkit",
            COMPOSIO_TEXT + " The verification FAQ lists sensitive scope verification as 10 business days.",
        ),
    }
    draft = valid_draft()
    draft["approval_wait"] = _claim("3-5 business days", "documented", ["e1"])
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        guide = client.get("/api/guides/example").json()
        assert guide["approval_wait"]["status"] == "unknown"
        assert guide["approval_wait"]["value"] is None
        note = guide["approval_wait"]["note"]
        assert "3-5 business days" in note
        assert "10 business days" in note
        assert "neither" in note.lower()


def test_a_dict_setup_path_still_saves(research_app):
    draft = valid_draft()
    draft["setup_path_value"] = {"value": "managed_or_own"}
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "completed"
        assert run["error_code"] is None


def test_a_missing_decision_uses_the_summary(research_app):
    draft = valid_draft()
    draft["decision"] = None
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        guide = client.get("/api/guides/example").json()
        assert len(guide["summary"]) >= 12
        assert len(guide["composio"]["decision"]) >= 12
        assert client.get(f"/api/research-runs/{response.json()['run_id']}").json()["status"] == "completed"


def test_null_action_lists_reuse_cited_steps(research_app):
    draft = valid_draft()
    draft["human_actions"] = None
    draft["blockers"] = None
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        guide = client.get("/api/guides/example").json()
        assert guide["human_actions"]
        assert guide["human_actions"][0]["body"]


def test_a_string_claim_is_not_stored_as_cited(research_app):
    draft = valid_draft()
    draft["auth_type"] = "Example uses OAuth 2.0."
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert "authentication type" in run["message"]
        assert client.get("/api/guides/example").status_code == 404
        assert len(research_app.state.fakes["model"].users) == 2


def test_malformed_model_output_is_rejected(research_app):
    research_app.state.fakes["model"].payload = "not json"
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["error_code"] == "malformed_output"
        assert client.get("/api/guides/example").status_code == 404


def test_credentials_in_model_output_are_not_stored(research_app):
    secret = "supersecretvalue12"
    research_app.state.fakes["model"].payload = json.dumps(valid_draft()).replace(
        "Example uses OAuth 2.0.",
        f"client_secret: {secret}",
    )
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["error_code"] == "credentials_in_output"
        assert secret not in json.dumps(run)
        assert client.get("/api/guides/example").status_code == 404


def test_duplicate_submission_joins_the_running_job(tmp_path, monkeypatch):
    import threading

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'guides.db'}")
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    monkeypatch.setenv("RESEARCH_INLINE", "false")
    from app.main import create_app

    class BlockingSearch(FakeSearch):
        def __init__(self) -> None:
            super().__init__()
            self.started = threading.Event()
            self.release = threading.Event()

        def search(self, query: str, *, limit: int):
            self.queries.append(query)
            self.started.set()
            assert self.release.wait(5)
            raise SearchError("down", "search_failed")

    application = create_app()
    search = BlockingSearch()
    application.state.research = replace(
        application.state.research,
        configured=True,
        inline=False,
        search=search,
        model=FakeModel(valid_draft()),
        reader=FakeReader({EXAMPLE_DOCS: ("Example OAuth", EXAMPLE_TEXT)}),
        unavailable_reason=None,
    )
    with TestClient(application) as client:
        first = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert first.status_code == 202
        assert search.started.wait(5)
        second = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert second.status_code == 200
        assert second.json()["code"] == "research_in_progress"
        assert second.json()["run_id"] == first.json()["run_id"]
        search.release.set()
        events = read_events(client, first.json()["run_id"])
        assert events[-1]["data"]["code"] == "search_failed"
        assert client.get("/api/guides/example").status_code == 404


def test_missing_human_action_does_not_save_a_guide(research_app):
    draft = valid_draft()
    draft["human_actions"] = []
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert "person" in run["message"]
        assert client.get("/api/guides/example").status_code == 404


def test_page_budget_keeps_provider_and_composio_pages():
    from app.research.pipeline import _select_urls

    hits = [SearchHit(f"Unrelated {index}", f"https://docs.composio.dev/page-{index}") for index in range(5)]
    hits.append(SearchHit("Vendor on Composio", "https://docs.composio.dev/toolkits/vendor"))
    hits.append(SearchHit("Vendor OAuth", "https://developer.vendor.example/docs/oauth"))
    hits.append(SearchHit("Box OAuth", "https://developer.box.com/guides/oauth"))
    hits.append(SearchHit("Vendor funding round", "https://finance.yahoo.com/news/vendor-raises"))
    hits.append(SearchHit("Vendor scopes", "https://developer.vendor.example/docs/scopes"))
    hits.append(SearchHit("Another Composio page", "https://docs.composio.dev/toolkits/vendor/extra"))
    urls = _select_urls(
        hits,
        "https://docs.vendor.example/register",
        4,
        app_name="Vendor",
        screen=lambda url: url,
    )
    assert urls[0] == "https://docs.vendor.example/register"
    assert "https://developer.vendor.example/docs/oauth" in urls
    assert "https://docs.composio.dev/toolkits/vendor" in urls
    assert "https://developer.vendor.example/docs/scopes" in urls
    assert "https://docs.composio.dev/toolkits/vendor/extra" not in urls
    assert not any("box.com" in url for url in urls)
    assert not any("yahoo.com" in url for url in urls)
    assert len(urls) == 4


def test_missing_steps_are_recovered_from_human_actions(research_app):
    draft = valid_draft()
    draft["steps"] = None
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "completed"
        guide = client.get("/api/guides/example").json()
        assert guide["steps"]


def test_an_off_topic_page_is_not_saved_as_the_app(research_app):
    box = "https://developer.box.com/guides/authentication/oauth2/oauth2-setup"
    research_app.state.fakes["search"].hits = [SearchHit("Box OAuth", box)]
    research_app.state.fakes["reader"].pages[box] = (
        "Setup with OAuth 2.0 - Box Dev Docs",
        "Log into your Box account and open the Developer Console.",
    )
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Acme", "docs_url": box})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert "Acme" in run["message"]
        assert client.get("/api/guides/acme").status_code == 404
        assert research_app.state.fakes["model"].systems == []


def test_a_documented_claim_that_drops_a_condition_is_inferred():
    from app.research.validate import EvidencePage, validate_draft

    pages = [
        EvidencePage(
            key="e1",
            url=EXAMPLE_DOCS,
            title="Example OAuth",
            text=EXAMPLE_TEXT + " Public connections must undergo a security review before being listed.",
            preferred=True,
            retrieved_at=datetime.now(timezone.utc),
        ),
        EvidencePage(
            key="e2",
            url=COMPOSIO_DOCS,
            title="Example toolkit",
            text=COMPOSIO_TEXT,
            preferred=True,
            retrieved_at=datetime.now(timezone.utc),
        ),
    ]
    draft = valid_draft()
    draft["blockers"] = [
        {
            "title": "Security review",
            "body": "Public connections must undergo a security review.",
            "status": "documented",
            "note": None,
            "evidence_ids": ["e1"],
        }
    ]
    checked = validate_draft(json.dumps(draft), pages)
    assert checked.blockers[0].status == "inferred"
    assert "before" in (checked.blockers[0].note or "").lower()


def test_restart_releases_a_dead_research_lock(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'guides.db'}")
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    monkeypatch.setenv("RESEARCH_INLINE", "true")
    from app.main import create_app
    from app.models import ActiveResearch, ResearchRun
    from app.research.store import utcnow

    first = create_app()
    with first.state.session_factory() as session:
        session.add(
            ResearchRun(
                id="dead-run",
                app_name="Example",
                normalized_name="example",
                docs_url=None,
                status="running",
                stage="searching",
                error_code=None,
                message=None,
                guide_slug=None,
                guide_created=False,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
        )
        session.add(ActiveResearch(normalized_name="example", run_id="dead-run"))
        session.commit()

    restarted = create_app()
    restarted.state.research = replace(
        restarted.state.research,
        configured=True,
        inline=True,
        search=FakeSearch(),
        model=FakeModel(valid_draft()),
        reader=FakeReader(
            {
                EXAMPLE_DOCS: ("Example OAuth", EXAMPLE_TEXT),
                COMPOSIO_DOCS: ("Example toolkit", COMPOSIO_TEXT),
            }
        ),
        unavailable_reason=None,
    )
    with TestClient(restarted) as client:
        old = client.get("/api/research-runs/dead-run").json()
        assert old["status"] == "failed"
        assert old["error_code"] == "interrupted"
        assert "restarted" in old["message"]
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        assert response.json()["run_id"] != "dead-run"
        assert response.json()["guide_created"] is True
        assert client.get("/api/guides/example").status_code == 200


def test_fenced_model_json_is_validated_and_saved(research_app):
    research_app.state.fakes["model"].payload = "Here is the guide:\n```json\n" + json.dumps(valid_draft()) + "\n```"
    with TestClient(research_app) as client:
        response = client.post(
            "/api/research-requests",
            json={"app_name": "Example", "docs_url": EXAMPLE_DOCS},
        )
        assert response.status_code == 202
        assert response.json()["guide_created"] is True
        guide = client.get("/api/guides/example")
        assert guide.status_code == 200
        assert guide.json()["auth_type"]["source_url"] == EXAMPLE_DOCS


def test_unsupported_inferred_step_is_not_stored(research_app):
    draft = valid_draft()
    draft["steps"].append(
        {
            "title": "Invented approval",
            "body": "The review board always approves this integration within one hour.",
            "status": "inferred",
            "note": None,
            "evidence_ids": ["e1"],
        }
    )
    research_app.state.fakes["model"].payload = draft
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        assert response.status_code == 202
        guide = client.get("/api/guides/example").json()
        bodies = " ".join(step["body"] for step in guide["steps"])
        assert "review board" not in bodies
        assert "Create an OAuth app in the developer settings." in bodies


def test_unreadable_pages_do_not_save_a_guide(research_app):
    class DeadReader:
        def read(self, url: str) -> FetchedPage:
            raise TransientFailure("The page request timed out.", "page_timeout")

    research_app.state.research = replace(research_app.state.research, reader=DeadReader())
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "insufficient_evidence"
        assert "could not be read" in run["message"]
        events = read_events(client, response.json()["run_id"])
        assert any("timed out" in event["data"]["message"] for event in events)
        assert client.get("/api/guides/example").status_code == 404


def test_provider_rejection_is_shown_on_the_run(research_app):
    research_app.state.fakes["model"].error = ModelError(
        "The model API rejected the API key. Check MODEL_API_KEY and MODEL_PROVIDER.",
        "model_failed",
    )
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["error_code"] == "model_failed"
        assert "MODEL_API_KEY" in run["message"]
        assert "No guide was saved." in run["message"]
        assert client.get("/api/guides/example").status_code == 404


def test_a_name_alone_starts_research(research_app):
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example"})
        assert response.status_code == 202
        assert response.json()["guide_created"] is True
        assert client.get("/api/guides/example").status_code == 200


def test_recheck_waits_for_promotion_and_survives_the_seed(research_app):
    with TestClient(research_app) as client:
        created = client.post(
            "/api/research-requests",
            json={"app_name": "Example", "docs_url": EXAMPLE_DOCS},
        )
        assert created.status_code == 202
        original = client.get("/api/guides/example").json()
        assert original["origin"] == "researched"
        assert original["pending_candidate"] is None

        research_app.state.fakes["model"].payload = {
            **valid_draft(),
            "summary": "Example uses OAuth 2.0. This wording belongs only on the candidate.",
        }
        recheck = client.post(
            "/api/guides/example/recheck",
            json={"docs_url": EXAMPLE_DOCS},
        )
        assert recheck.status_code == 202
        assert recheck.json()["guide_created"] is False
        live = client.get("/api/guides/example").json()
        assert live["summary"] == original["summary"]
        assert live["pending_candidate"]["run_id"] == recheck.json()["run_id"]

        candidate = client.get("/api/guides/example/candidate").json()
        assert "Summary" in candidate["changed_fields"]
        assert candidate["guide"]["summary"] != original["summary"]
        assert "wording belongs only on the candidate" in candidate["guide"]["summary"]

        promoted = client.post("/api/guides/example/candidate/promote")
        assert promoted.status_code == 200
        assert "wording belongs only on the candidate" in promoted.json()["summary"]
        assert promoted.json()["origin"] == "researched"
        assert promoted.json()["pending_candidate"] is None
        assert client.get("/api/guides/example/candidate").status_code == 404

    from app.seed import seed_database

    seed_database(research_app.state.engine)
    with TestClient(research_app) as client:
        assert "wording belongs only on the candidate" in client.get("/api/guides/example").json()["summary"]


def test_seed_does_not_overwrite_a_promoted_guide(research_app):
    from sqlalchemy import select

    from app.models import Guide
    from app.seed import seed_database

    with research_app.state.session_factory() as session:
        guide = session.scalar(select(Guide).where(Guide.slug == "github"))
        guide.origin = "researched"
        guide.summary = "Promoted GitHub summary stays."
        session.commit()
    seed_database(research_app.state.engine)
    with TestClient(research_app) as client:
        body = client.get("/api/guides/github").json()
        assert body["summary"] == "Promoted GitHub summary stays."
        assert body["origin"] == "researched"


def test_recheck_without_keys_leaves_the_guide_alone(client: TestClient):
    before = client.get("/api/guides/github").json()["summary"]
    response = client.post("/api/guides/github/recheck", json={"docs_url": "https://docs.github.com"})
    assert response.status_code == 503
    assert response.json()["guide_created"] is False
    assert client.get("/api/guides/github").json()["summary"] == before
    assert client.get("/api/guides/github/candidate").status_code == 404


def test_discard_drops_a_candidate_without_editing_the_guide(research_app):
    with TestClient(research_app) as client:
        client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        original = client.get("/api/guides/example").json()["summary"]
        research_app.state.fakes["model"].payload = {
            **valid_draft(),
            "summary": "Example uses OAuth 2.0. Discard should leave the saved summary alone.",
        }
        client.post("/api/guides/example/recheck", json={"docs_url": EXAMPLE_DOCS})
        discarded = client.post("/api/guides/example/candidate/discard")
        assert discarded.status_code == 200
        assert discarded.json()["status"] == "discarded"
        assert client.get("/api/guides/example").json()["summary"] == original
        assert client.get("/api/guides/example").json()["pending_candidate"] is None


def test_timeout_fails_the_run(research_app):
    research_app.state.research = replace(research_app.state.research, deadline_seconds=0)
    with TestClient(research_app) as client:
        response = client.post("/api/research-requests", json={"app_name": "Example", "docs_url": EXAMPLE_DOCS})
        run = client.get(f"/api/research-runs/{response.json()['run_id']}").json()
        assert run["status"] == "failed"
        assert run["error_code"] == "timeout"
        assert client.get("/api/guides/example").status_code == 404
