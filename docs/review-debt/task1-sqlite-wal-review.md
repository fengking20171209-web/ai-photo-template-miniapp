# Task 1: SQLite WAL Review

**Status:** CONDITIONALLY_ACCEPTED_REMOTE_REVIEW_PENDING
**Block Reason:** BLOCKED_BY_UPSTREAM_RATE_LIMIT

## Commit Diff

```diff
diff --git a/backend/database.py b/backend/database.py
index 36b2637..f717e1e 100644
--- a/backend/database.py
+++ b/backend/database.py
@@ -16,9 +16,12 @@ engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_ar
 if DATABASE_URL.startswith("sqlite"):
     @event.listens_for(engine, "connect")
     def set_sqlite_pragma(dbapi_connection, connection_record):
+        if ":memory:" in DATABASE_URL or DATABASE_URL in ("sqlite://", "sqlite:///"):
+            return
         cursor = dbapi_connection.cursor()
         cursor.execute("PRAGMA journal_mode=WAL")
         cursor.execute("PRAGMA synchronous=NORMAL")
+        cursor.execute("PRAGMA busy_timeout=5000")
         cursor.close()
 
 SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
diff --git a/tests/backend/test_db_wal.py b/tests/backend/test_db_wal.py
index 368dd2e..91f6396 100644
--- a/tests/backend/test_db_wal.py
+++ b/tests/backend/test_db_wal.py
@@ -1,53 +1,65 @@
 import os
-os.environ["DATABASE_URL"] = "sqlite:///./test_wal.db"
-
 import asyncio
 import pytest
 import time
-from sqlalchemy import Column, Integer, String
-from backend.database import SessionLocal, Base, engine
+import logging
+from sqlalchemy import Column, Integer, String, create_engine, event, text
+from sqlalchemy.orm import sessionmaker
+
+logger = logging.getLogger(__name__)
+
+# Do not set os.environ["DATABASE_URL"] here to prevent import coupling.
+
+from backend.database import Base
 
 class DummyModel(Base):
     __tablename__ = "dummy_wal_table"
     id = Column(Integer, primary_key=True, index=True)
     value = Column(String, index=True)
 
-@pytest.fixture(scope="session", autouse=True)
-def setup_database():
-    # Setup test database
+TEST_DB_PATH = "./test_wal_pytest.db"
+TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
+
+@pytest.fixture(scope="session")
+def test_engine():
+    import backend.database as db
+    
+    # Construct an independent engine
+    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
+    
+    # Temporarily override DATABASE_URL in db module so set_sqlite_pragma passes the memory check
+    original_url = getattr(db, "DATABASE_URL", "")
+    db.DATABASE_URL = TEST_DATABASE_URL
+    
+    if hasattr(db, "set_sqlite_pragma"):
+        event.listen(engine, "connect", db.set_sqlite_pragma)
+        
     Base.metadata.create_all(bind=engine)
-    yield
-    # Teardown
+    
+    yield engine
+    
     Base.metadata.drop_all(bind=engine)
-    # clean up file
-    if os.path.exists("./test_wal.db"):
-        try:
-            os.remove("./test_wal.db")
-        except:
-            pass
-    if os.path.exists("./test_wal.db-shm"):
-        try:
-            os.remove("./test_wal.db-shm")
-        except:
-            pass
-    if os.path.exists("./test_wal.db-wal"):
-        try:
-            os.remove("./test_wal.db-wal")
-        except:
-            pass
+    engine.dispose()
+    db.DATABASE_URL = original_url
+    
+    for ext in ["", "-shm", "-wal"]:
+        path = f"{TEST_DB_PATH}{ext}"
+        if os.path.exists(path):
+            try:
+                os.remove(path)
+            except Exception as e:
+                logger.error(f"Failed to remove {path}: {e}")
 
-def db_write_read(worker_id: int, iterations: int):
-    # Simulate DB load by writing and reading in a synchronous function
+def db_write_read(engine, worker_id: int, iterations: int):
+    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
     for i in range(iterations):
         db = SessionLocal()
         try:
-            # write
             new_record = DummyModel(value=f"worker_{worker_id}_iter_{i}")
             db.add(new_record)
             db.commit()
             db.refresh(new_record)
             
-            # read
             record = db.query(DummyModel).filter(DummyModel.id == new_record.id).first()
             assert record is not None
             assert record.value == f"worker_{worker_id}_iter_{i}"
@@ -55,21 +67,31 @@ def db_write_read(worker_id: int, iterations: int):
             db.close()
 
 @pytest.mark.asyncio
-async def test_concurrent_db_access():
+async def test_concurrent_db_access(test_engine):
     workers = 5
     iterations = 50
     
     start_time = time.time()
-    
     loop = asyncio.get_running_loop()
     tasks = []
     
     for worker_id in range(workers):
         tasks.append(
-            loop.run_in_executor(None, db_write_read, worker_id, iterations)
+            loop.run_in_executor(None, db_write_read, test_engine, worker_id, iterations)
         )
         
     await asyncio.gather(*tasks)
-    
     duration = time.time() - start_time
     print(f"\nConcurrent write/read finished in {duration:.2f} seconds")
+
+def test_pragmas_are_set(test_engine):
+    with test_engine.connect() as conn:
+        journal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
+        assert journal_mode is not None
+        assert journal_mode.lower() == "wal"
+        
+        synchronous = conn.execute(text("PRAGMA synchronous;")).scalar()
+        assert synchronous in (1, 2)
+        
+        busy_timeout = conn.execute(text("PRAGMA busy_timeout;")).scalar()
+        assert busy_timeout == 5000

```
