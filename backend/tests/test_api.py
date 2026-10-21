from pathlib import Path

from fastapi.testclient import TestClient


def _statuses(value, found: list[str]) -> None:
    if isinstance(value, dict):
        if "status" in value:
            found.append(value["status"])
        for child in value.values():
            _statuses(child, found)
    elif isinstance(value, list):
        for child in value:
            _statuses(child, found)

EXPECTED_COUNTS = {
    "github": {"steps": 7, "blockers": 8, "human_actions": 5, "prerequisites": 3},
    "slack": {"steps": 8, "blockers": 7, "human_actions": 6, "prerequisites": 3},
    "google-calendar": {"steps": 8, "blockers": 8, "human_actions": 6, "prerequisites": 4},
}


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "research": "unavailable"}


def test_directory_lists_three_distinct_guides(client: TestClient):
    response = client.get("/api/guides")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    slugs = [guide["slug"] for guide in body["guides"]]
    assert slugs == ["github", "google-calendar", "slack"]
    assert all(guide["tested"] is False for guide in body["guides"])
    assert {guide["auth_type"]["value"] for guide in body["guides"]} == {"OAuth 2.0"}


def test_search_is_case_insensitive_and_empty_query_is_honest(client: TestClient):
    calendar = client.get("/api/guides", params={"q": "CALENDAR"})
    assert [guide["slug"] for guide in calendar.json()["guides"]] == ["google-calendar"]

    quota = client.get("/api/guides", params={"q": "quota"})
    assert [guide["slug"] for guide in quota.json()["guides"]] == [
        "github",
        "google-calendar",
        "slack",
    ]

    missing = client.get("/api/guides", params={"q": "not-a-provider"})
    assert missing.status_code == 200
    assert missing.json() == {"guides": [], "count": 0}

    blank = client.get("/api/guides", params={"q": "   "})
    assert blank.json()["count"] == 3


def test_setup_path_filter(client: TestClient):
    own_app = client.get("/api/guides", params={"path": "own_app_unless_confirmed"})
    assert own_app.json() == {"guides": [], "count": 0}

    managed = client.get("/api/guides", params={"path": "managed_or_own"})
    assert [guide["slug"] for guide in managed.json()["guides"]] == [
        "github",
        "google-calendar",
        "slack",
    ]

    rejected = client.get("/api/guides", params={"path": "magic"})
    assert rejected.status_code == 400
    assert rejected.json()["detail"]["code"] == "invalid_path"


def test_guide_pages_are_persistent_and_separate_claims(client: TestClient):
    for slug, counts in EXPECTED_COUNTS.items():
        response = client.get(f"/api/guides/{slug}")
        assert response.status_code == 200
        body = response.json()
        assert body["slug"] == slug
        assert body["tested"] is False
        assert body["last_checked"] == "2026-10-21"
        assert body["execution_note"]
        assert body["composio"]["redirect_uri"]["value"] == (
            "https://backend.composio.dev/api/v3/toolkits/auth/callback"
        )
        for field, expected in counts.items():
            assert len(body[field]) == expected
            positions = [item["position"] for item in body[field]]
            assert positions == list(range(1, expected + 1))
        titles = [step["title"] for step in body["steps"]]
        assert len(titles) == len(set(titles))
        urls = [source["url"] for source in body["sources"]]
        assert urls and all(url.startswith("https://") for url in urls)
        assert len(urls) == len(set(urls))
        statuses: list[str] = []
        _statuses(body, statuses)
        assert statuses
        assert "verified" not in statuses
        assert "documented" in statuses
        assert "uncertain" in statuses
        assert body["auth_type"]["source_url"] is None
        assert body["steps"][0]["source_url"] is None


def test_provider_waits_are_not_invented(client: TestClient):
    github = client.get("/api/guides/github").json()
    slack = client.get("/api/guides/slack").json()
    calendar = client.get("/api/guides/google-calendar").json()

    github_wait = github["approval_wait"]["value"].lower()
    assert github_wait.startswith("unknown.")
    assert "business day" not in github_wait
    assert "week" not in github_wait
    assert github["setup_path"]["value"] == "managed_or_own"

    slack_wait = slack["approval_wait"]["value"]
    assert "Unknown for creating a Slack app" in slack_wait
    assert "Marketplace review is not required to create an app" in slack_wait
    assert "up to 10 business days" in slack_wait
    assert "up to 10 weeks for new submissions" in slack_wait
    assert "6 weeks for published apps" in slack_wait
    assert "owning workspace" in slack_wait
    assert slack["setup_path"]["value"] == "managed_or_own"

    calendar_wait = calendar["approval_wait"]["value"]
    assert "3-5 business days" in calendar_wait
    assert "10 business days" in calendar_wait
    assert "otherwise unknown" in calendar_wait.lower()
    assert "2-3 business days" not in calendar_wait
    assert "several weeks" not in calendar_wait.lower()
    assert "6 weeks" not in calendar_wait.lower()
    assert calendar["approval_wait"]["status"] == "uncertain"
    assert calendar["setup_path"]["value"] == "managed_or_own"
    assert calendar["setup_path"]["status"] == "documented"
    assert calendar["composio"]["managed"]["status"] == "documented"
    combined = " ".join(
        [
            calendar["summary"],
            calendar["composio"]["decision"],
            calendar["setup_path"]["label"],
            calendar["setup_path"]["note"] or "",
            calendar["composio"]["managed"]["value"],
            calendar["composio"]["bring_your_own"]["value"],
        ]
    ).lower()
    assert "own app until managed access is confirmed" not in combined
    assert "not a prerequisite" in calendar["composio"]["decision"].lower()
    assert "does not require you to bring your own app" in calendar["composio"]["bring_your_own"]["value"].lower()
    assert "googlecalendar" in calendar["composio"]["managed"]["value"].lower()
    source_urls = [source["url"] for source in calendar["sources"]]
    assert "https://docs.composio.dev/toolkits/managed-auth" in source_urls
    assert "https://docs.composio.dev/toolkits/googlecalendar" in source_urls
    assert "https://support.google.com/cloud/answer/13463817" in source_urls
    assert not any("quickstart" in url for url in source_urls)
    assert any(step["status"] == "uncertain" for step in calendar["steps"])
    assert "verified" not in [calendar["setup_path"]["status"], calendar["approval_wait"]["status"]]


def test_unknown_guide_is_not_found(client: TestClient):
    response = client.get("/api/guides/notion")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "not_found"


def test_research_is_unavailable_and_creates_nothing(client: TestClient):
    before = client.get("/api/guides").json()["count"]
    response = client.post(
        "/api/research-requests",
        json={"app_name": "  Notion  ", "docs_url": "https://developers.notion.com"},
    )
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "research_unavailable"
    assert body["guide_created"] is False
    assert body["app_name"] == "Notion"
    assert "model provider" in body["message"]
    assert client.get("/api/guides").json()["count"] == before
    assert client.get("/api/guides/notion").status_code == 404


def test_research_rejects_blank_names_and_bad_urls(client: TestClient):
    blank = client.post("/api/research-requests", json={"app_name": "   "})
    assert blank.status_code == 422
    bad_url = client.post(
        "/api/research-requests",
        json={"app_name": "Notion", "docs_url": "not a url"},
    )
    assert bad_url.status_code == 422


def test_research_module_does_not_call_a_provider():
    source = Path(__file__).resolve().parents[1].joinpath("app/routers/research.py").read_text().lower()
    for banned in ("openai", "anthropic", "httpx", "requests.", "urllib"):
        assert banned not in source


def test_seed_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'guides.db'}")
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    from app.main import create_app

    create_app()
    application = create_app()
    with TestClient(application) as client:
        github = client.get("/api/guides/github").json()
        assert len(github["steps"]) == EXPECTED_COUNTS["github"]["steps"]
        assert client.get("/api/guides").json()["count"] == 3
