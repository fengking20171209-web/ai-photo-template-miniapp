from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class PromptDraftCreate(BaseModel):
    title: str
    content: str
    system_message: Optional[str] = None
    parameters_json: Optional[Dict[str, Any]] = None
    prompt_id: Optional[int] = None

class PromptDraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    system_message: Optional[str] = None
    parameters_json: Optional[Dict[str, Any]] = None

class PublishDraftRequest(BaseModel):
    change_note: Optional[str] = None
    created_by: Optional[str] = None

class TaskSubmit(BaseModel):
    title: str
    task_type: str
    input_json: Optional[Dict[str, Any]] = None
    prompt_version_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    chain_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    task_type: str
    status: str
    input_json: Optional[Dict[str, Any]] = None
    output_json: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    prompt_version_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    chain_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PromptVersionResponse(BaseModel):
    id: int
    prompt_id: int
    version: int
    content: str
    system_message: Optional[str] = None
    parameters_json: Optional[Dict[str, Any]] = None
    change_note: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool
    content_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PromptDraftResponse(BaseModel):
    id: int
    prompt_id: Optional[int] = None
    title: str
    content: str
    system_message: Optional[str] = None
    parameters_json: Optional[Dict[str, Any]] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
