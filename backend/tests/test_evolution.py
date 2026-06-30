import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base
from backend.dependencies import get_db
from backend.models import Prompt, PromptVersion, Asset

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_evolution.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    # Scope the dependency override to this module's tests so it does not leak
    # the test_evolution.db binding into other test files (which then fail with
    # "no such table" once this module's teardown drops the tables).
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    prompt = Prompt(name="Test Prompt")
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    version = PromptVersion(prompt_id=prompt.id, version=1, content="Draw a cat", is_active=True)
    db.add(version)
    db.commit()
    db.refresh(version)

    prompt.current_version_id = version.id
    db.commit()
    
    asset = Asset(asset_type="image", file_path="test.jpg")
    db.add(asset)
    db.commit()
    
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

def test_create_run():
    # Setup test DB will have prompt_id=1, version_id=1
    response = client.post("/api/prompt-evolution/runs?prompt_id=1&base_version_id=1")
    assert response.status_code == 200
    data = response.json()
    assert data["prompt_id"] == 1
    assert data["base_version_id"] == 1
    assert data["status"] == "completed"

def test_promote_candidate():
    client.post("/api/prompt-evolution/runs?prompt_id=1&base_version_id=1")
    
    # get candidates
    candidates_resp = client.get("/api/prompt-evolution/runs/1/candidates")
    candidates = candidates_resp.json()
    assert len(candidates) > 0
    candidate_id = candidates[0]["id"]
    
    # promote
    promote_resp = client.post(f"/api/prompt-evolution/candidates/{candidate_id}/promote", json={"change_note": "Promoting test", "created_by": "test"})
    assert promote_resp.status_code == 200
    promote_data = promote_resp.json()
    assert promote_data["status"] == "promoted"
    assert promote_data["promoted_version_id"] is not None

def test_reject_candidate():
    client.post("/api/prompt-evolution/runs?prompt_id=1&base_version_id=1")
    
    candidates_resp = client.get("/api/prompt-evolution/runs/1/candidates")
    candidate_id = candidates_resp.json()[0]["id"]
    
    reject_resp = client.post(f"/api/prompt-evolution/candidates/{candidate_id}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

def test_evaluation_records():
    eval_payload = {
        "asset_id": 1,
        "prompt_version_id": 1,
        "score": 5,
        "feedback": "Great image"
    }
    eval_resp = client.post("/api/prompt-evolution/evaluations", json=eval_payload)
    assert eval_resp.status_code == 200
    assert eval_resp.json()["score"] == 5
    
    get_resp = client.get("/api/prompt-evolution/evaluations/asset/1")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) == 1
