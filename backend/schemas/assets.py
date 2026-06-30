from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import os

class AssetBase(BaseModel):
    task_id: Optional[int] = None
    asset_type: str
    mime_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: str
    file_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if '..' in v or v.startswith('/') or v.startswith('\\') or ':' in v:
            raise ValueError("Invalid file_path: directory traversal or absolute paths are not allowed.")
        return v

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class AssetResponse(AssetBase):
    id: int
    task_chain_id: Optional[int] = None
    prompt_version_id: Optional[int] = None
    is_favorite: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    file_path: str = Field(exclude=True)

    model_config = ConfigDict(from_attributes=True)

class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    page: int
    size: int
