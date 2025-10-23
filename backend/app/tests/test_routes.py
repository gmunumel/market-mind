import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
import app.api.deps as deps_module
import app.api.routes.chats as chats_routes
import app.db as db_package
import app.db.session as db_session
from app.core.config import get_settings
from app.core.rate_limiter import RateLimiter
from app.db import Base
from app.services import AgentService


@pytest.fixture()
def client(tmp_path, monkeypatch):
    os.environ["ENVIRONMENT"] = "test"
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["CHROMA_PERSIST_DIRECTORY"] = str(tmp_path / "chroma")

    get_settings.cache_clear()
    settings = get_settings()

    engine = create_engine(settings.database_url, future=True)
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[deps_module.get_db] = override_get_db

    monkeypatch.setattr(main, "settings", settings, raising=False)
    monkeypatch.setattr(db_session, "settings", settings, raising=False)
    monkeypatch.setattr(db_session, "engine", engine, raising=False)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal, raising=False)
    monkeypatch.setattr(db_package, "engine", engine, raising=False)
    monkeypatch.setattr(db_package, "SessionLocal", TestingSessionLocal, raising=False)

    monkeypatch.setattr(deps_module, "settings", settings, raising=False)
    monkeypatch.setattr(deps_module, "SessionLocal", TestingSessionLocal, raising=False)
    monkeypatch.setattr(
        deps_module,
        "rate_limiter",
        RateLimiter(settings.hourly_request_limit, settings.daily_request_limit),
        raising=False,
    )

    test_agent = AgentService(settings=settings)
    monkeypatch.setattr(chats_routes, "settings", settings, raising=False)
    monkeypatch.setattr(chats_routes, "agent_service", test_agent, raising=False)
    monkeypatch.setattr(main, "engine", engine, raising=False)

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()


def test_create_chat_and_send_message(client):
    create_resp = client.post("/chats", json={"title": "Macro Outlook"})
    assert create_resp.status_code == 201
    chat_id = create_resp.json()["id"]

    message_resp = client.post(
        f"/chats/{chat_id}/messages",
        json={"content": "What is the market sentiment on BTC today?"},
        headers={"X-User-Id": "test-user"},
    )
    assert message_resp.status_code == 200
    body = message_resp.json()
    assert body["message"]["content"] == "What is the market sentiment on BTC today?"
    assert body["ai_response"]["role"] == "assistant"
    assert "placeholder response" in body["ai_response"]["content"]


def test_list_chats_returns_created_chat(client):
    create_resp = client.post("/chats", json={"title": "Equities"})
    chat_id = create_resp.json()["id"]

    list_resp = client.get("/chats")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert any(chat["id"] == chat_id for chat in data)
