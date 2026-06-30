"""Pydantic models for image search query parameters and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchParams(BaseModel):
    """Validated query parameters for image search."""

    model_config = ConfigDict(from_attributes=True)

    q: Optional[str] = Field(None, description="Search keyword for title and prompt")
    tags: Optional[List[str]] = Field(None, description="Tags that must all be present")
    start_date: Optional[datetime] = Field(None, description="Start datetime for created_at")
    end_date: Optional[datetime] = Field(None, description="End datetime for created_at")
    page: int = Field(1, ge=1, description="Page number, starting from 1")
    limit: int = Field(20, ge=1, le=100, description="Items per page, max 100")


class ImageOut(BaseModel):
    """Public image fields returned by search results."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    image_url: str
    thumbnail_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime


class SearchResponse(BaseModel):
    """Paginated image search response."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    pages: int
    items: List[ImageOut]


class TemplateSearchParams(BaseModel):
    """Validated query parameters for template search."""

    q: Optional[str] = Field(None, description="Search keyword for title, style, scene, clothing")
    category: Optional[str] = Field(None, description="Filter by template category")
    page: int = Field(1, ge=1, description="Page number, starting from 1")
    limit: int = Field(20, ge=1, le=100, description="Items per page, max 100")
    sort: str = Field("title", description="Sort field: title | template_id | category")


class TemplateSearchItem(BaseModel):
    """Template summary returned by template search."""

    template_id: str
    category: str
    title: str
    style: str
    ratio: str
    face_lock: bool
    scene: str
    clothing: str
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    price: Optional[float] = Field(None, description="Template price in CNY (deprecated, kept for backward compatibility)")
    is_free: Optional[bool] = Field(None, description="Whether the template is free (deprecated, kept for backward compatibility)")


class TemplateSearchResponse(BaseModel):
    """Paginated template search response."""

    total: int
    page: int
    pages: int
    items: List[TemplateSearchItem]
