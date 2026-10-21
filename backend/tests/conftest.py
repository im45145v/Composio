import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "guides.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_ON_STARTUP", "true")
    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
