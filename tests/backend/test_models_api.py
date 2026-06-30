"""Tests for the model-persona library API and analytics event endpoint.

Uses a scoped get_db override against a dedicated SQLite file so it never
touches the real gallery DB. Override + tables are torn down per-module.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base
from backend.dependencies import get_db

DB_URL = "sqlite:///./test_models_api.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = _override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


def _create(name="CC 模特", tags=None):
    return client.post("/api/models", json={
        "name": name,
        "reference_image": "data:image/png;base64,iVBORw0KGgo=",
        "identity_prompt": "same face",
        "negative_prompt": "face change",
        "tags": tags or ["韩系", "清纯"],
    })


def test_model_crud_lifecycle():
    # create
    r = _create()
    assert r.status_code == 200
    m = r.json()
    assert m["id"].startswith("m_")
    assert m["name"] == "CC 模特"
    assert m["usage_count"] == 0
    mid = m["id"]

    # list
    lst = client.get("/api/models").json()
    assert any(x["id"] == mid for x in lst["models"])

    # use -> usage_count++
    u = client.post(f"/api/models/{mid}/use").json()
    assert u["usage_count"] == 1

    # update
    up = client.put(f"/api/models/{mid}", json={"name": "CC v2", "tags": ["御姐"], "identity_prompt": "x", "negative_prompt": "y"}).json()
    assert up["name"] == "CC v2"
    assert up["tags"] == ["御姐"]

    # delete
    d = client.delete(f"/api/models/{mid}").json()
    assert d["ok"] is True
    assert all(x["id"] != mid for x in client.get("/api/models").json()["models"])


def test_update_missing_model_404():
    r = client.put("/api/models/nope", json={"name": "x"})
    assert r.status_code == 404


def test_reference_image_too_large_rejected():
    big = "data:image/png;base64," + ("A" * (9 * 1024 * 1024))
    r = client.post("/api/models", json={"name": "big", "reference_image": big})
    assert r.status_code == 413


def test_analytics_event_records_and_validates():
    ok = client.post("/analytics/event", data={"event_type": "generate", "session_id": "s1"})
    assert ok.status_code == 200
    assert ok.json()["ok"] is True
    # missing event_type -> ok:false
    bad = client.post("/analytics/event", data={"session_id": "s1"})
    assert bad.json()["ok"] is False
