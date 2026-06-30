import os
import sqlite3
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Prompt, PromptVersion, Task, TaskChain, Asset
from backend import crud_assets
from backend.schemas.assets import AssetCreate, AssetUpdate

TEST_DB_URL = "sqlite:///./test_phase3a.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    if os.path.exists("./test_phase3a.db"):
        os.remove("./test_phase3a.db")
    
    # In order to test 001->004, we'll use Base.metadata.create_all for 001
    # Actually, if we just use create_all, we don't need to run 002, 003, 004 manually because models.py has all tables.
    # But to "test migrations", we should at least execute 004_assets.sql over a DB that has 001-003.
    # Since we don't have 001, we can create_all first without Asset, but we already added Asset to models.
    # So create_all creates everything. We'll simulate migration by running 004_assets.sql directly after dropping assets if exists.
    
    Base.metadata.create_all(bind=engine)
    
    conn = sqlite3.connect("./test_phase3a.db")
    conn.execute("DROP TABLE IF EXISTS assets")
    with open(os.path.join(os.path.dirname(__file__), "../../backend/migrations/004_assets.sql"), "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()

    db = TestingSessionLocal()
    yield db
    db.close()
    engine.dispose()
    
    if os.path.exists("./test_phase3a.db"):
        os.remove("./test_phase3a.db")

def test_migration_001_to_004(test_db):
    from sqlalchemy import text
    result = test_db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    tables = [r[0] for r in result]
    assert "assets" in tables

def test_asset_crud_and_pagination(test_db):
    # Setup prompt version & task
    prompt = Prompt(name="Test", category="Test")
    test_db.add(prompt)
    test_db.commit()

    pv = PromptVersion(prompt_id=prompt.id, version=1, content="Test")
    test_db.add(pv)
    test_db.commit()

    chain = TaskChain(name="Test Chain")
    test_db.add(chain)
    test_db.commit()

    task1 = Task(title="T1", task_type="t", prompt_version_id=pv.id, chain_id=chain.id)
    task2 = Task(title="T2", task_type="t", prompt_version_id=pv.id, chain_id=chain.id)
    test_db.add(task1)
    test_db.add(task2)
    test_db.commit()

    # Create assets
    asset1_in = AssetCreate(
        task_id=task1.id,
        asset_type="image",
        file_path="safe/path/1.png",
        source="generated"
    )
    asset1 = crud_assets.create_asset(test_db, asset1_in)
    assert asset1.id is not None
    assert asset1.task_id == task1.id
    
    # Test Traceability (Automatically populated)
    assert asset1.task_chain_id == chain.id
    assert asset1.prompt_version_id == pv.id

    asset2_in = AssetCreate(
        task_id=task2.id,
        asset_type="image",
        file_path="safe/path/2.png",
        source="generated"
    )
    crud_assets.create_asset(test_db, asset2_in)

    # Read
    fetched = crud_assets.get_asset(test_db, asset1.id)
    assert fetched.id == asset1.id

    # Pagination
    items, total = crud_assets.get_assets(test_db, skip=0, limit=1)
    assert len(items) == 1
    assert total == 2

    # Filter
    items, total = crud_assets.get_assets(test_db, source="generated")
    assert total == 2

    # Update
    crud_assets.update_asset(test_db, asset1.id, AssetUpdate(title="New Title"))
    updated = crud_assets.get_asset(test_db, asset1.id)
    assert updated.title == "New Title"

    # Soft Delete
    crud_assets.soft_delete_asset(test_db, asset1.id)
    assert crud_assets.get_asset(test_db, asset1.id) is None

    # Total should be 1 now
    items, total = crud_assets.get_assets(test_db)
    assert total == 1

    # Restore
    crud_assets.restore_asset(test_db, asset1.id)
    assert crud_assets.get_asset(test_db, asset1.id) is not None

def test_traceability_uploaded_no_task(test_db):
    asset_in = AssetCreate(
        asset_type="image",
        file_path="safe/upload.png",
        source="uploaded",
        metadata_json={"user": "admin"}
    )
    asset = crud_assets.create_asset(test_db, asset_in)
    assert asset.source == "uploaded"
    assert asset.task_id is None

def test_traceability_uploaded_no_metadata_fails(test_db):
    asset_in = AssetCreate(
        asset_type="image",
        file_path="safe/upload2.png",
        source="uploaded"
    )
    with pytest.raises(ValueError):
        crud_assets.create_asset(test_db, asset_in)

def test_traceability_generated_no_task_fails(test_db):
    asset_in = AssetCreate(
        asset_type="image",
        file_path="safe/gen.png",
        source="generated"
    )
    with pytest.raises(ValueError):
        crud_assets.create_asset(test_db, asset_in)

def test_security_directory_traversal():
    with pytest.raises(ValueError):
        AssetCreate(
            task_id=1,
            asset_type="image",
            file_path="../etc/passwd"
        )
    with pytest.raises(ValueError):
        AssetCreate(
            task_id=1,
            asset_type="image",
            file_path="/etc/passwd"
        )
    with pytest.raises(ValueError):
        AssetCreate(
            task_id=1,
            asset_type="image",
            file_path="C:\\Windows\\System32\\cmd.exe"
        )

def test_regression(test_db):
    # Just check if we can still query legacy tables without issue
    from backend.models import Image
    test_db.query(Image).count()
