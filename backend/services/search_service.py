"""Image search service layer.

Handles dynamic query construction for image search with filters,
pagination, and tag queries compatible with both PostgreSQL and SQLite.
"""

import math
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, String

from backend.models import Image
from backend.schemas.search import SearchParams, ImageOut, SearchResponse


def search_images(db: Session, params: SearchParams) -> SearchResponse:
    """Search images with dynamic filters and pagination."""
    query = db.query(Image)
    filters = []

    # Keyword search: match title OR prompt (case-insensitive)
    if params.q:
        escaped_q = params.q.replace("%", "\\%").replace("_", "\\_")
        keyword = f"%{escaped_q}%"
        filters.append(
            or_(
                Image.title.like(keyword, escape="\\"),
                Image.prompt.like(keyword, escape="\\"),
            )
        )

    # Tag filter: check JSON array contains all specified tags.
    # Uses string-contains which works on both SQLite and PostgreSQL.
    # Escapes double quotes in tag values to prevent filter corruption.
    if params.tags:
        for tag in params.tags:
            safe_tag = tag.replace('"', '\\"')
            filters.append(
                func.cast(Image.tags, String).like(f'%"{safe_tag}"%')
            )

    # Date range filter
    date_filters = []
    if params.start_date:
        date_filters.append(Image.created_at >= params.start_date)
    if params.end_date:
        date_filters.append(Image.created_at <= params.end_date)
    if date_filters:
        filters.append(and_(*date_filters))

    if filters:
        query = query.filter(and_(*filters))

    total = query.with_entities(func.count(Image.id)).scalar()

    offset = (params.page - 1) * params.limit
    query = query.order_by(Image.created_at.desc())
    query = query.offset(offset).limit(params.limit)

    images: List[Image] = query.all()
    items = [ImageOut.model_validate(img) for img in images]
    pages = math.ceil(total / params.limit) if total > 0 else 1

    return SearchResponse(
        total=total,
        page=params.page,
        pages=pages,
        items=items,
    )
