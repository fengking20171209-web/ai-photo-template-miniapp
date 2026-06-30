"""FastAPI dependency injection."""
from sqlalchemy.orm import Session
from backend.database import SessionLocal


def get_db() -> Session:
    """Yield a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
