"""Tests for gallery listing (mock filtering) and bulk delete.

Scoped get_db override against a dedicated SQLite file. Uses http image URLs
so deletion never touches the local filesystem.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base
from backend.dependencies import get_db
from backend.models import Image

DB_URL = "sqlite:///./test_gallery.db"
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


def _seed():
    db = TestingSessionLocal()
    real = Image(title="real", prompt="p", image_url="https://cdn/x.png", thumbnail_url="https://cdn/x.png", source="agnes")
    mock = Image(title="mock", prompt="p", image_url="cos://local/m.png", thumbnail_url="/placeholder.svg", source="mock")
    db.add_all([real, mock])
    db.commit()
    db.refresh(real)
    rid = real.id
    db.close()
    return rid


def test_recent_excludes_mock():
    _seed()
    items = client.get("/images/recent").json()["items"]
    assert len(items) == 1
    assert items[0]["source"] == "agnes"
    assert all(i["thumbnail_url"] != "/placeholder.svg" for i in items)


def test_bulk_delete_removes_and_validates():
    rid = _seed()
    # empty ids -> 400
    assert client.post("/images/bulk-delete", json={"ids": []}).status_code == 400
    # delete the real one
    resp = client.post("/images/bulk-delete", json={"ids": [rid]}).json()
    assert resp["deleted"] == 1
    assert client.get("/images/recent").json()["items"] == []
