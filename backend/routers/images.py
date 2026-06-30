"""Image search and retrieval endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.schemas.search import SearchParams, SearchResponse
from backend.services.search_service import search_images

router = APIRouter()


@router.get("/", response_model=SearchResponse)
def get_images(
    q: Optional[str] = Query(None, description="Search keyword for title and prompt"),
    tags: Optional[List[str]] = Query(None, description="Tags that must all be present"),
    start_date: Optional[datetime] = Query(None, description="Start datetime for created_at"),
    end_date: Optional[datetime] = Query(None, description="End datetime for created_at"),
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    limit: int = Query(20, ge=1, le=100, description="Items per page, max 100"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search images with optional filters and pagination."""

    params = SearchParams(
        q=q,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return search_images(db, params)
