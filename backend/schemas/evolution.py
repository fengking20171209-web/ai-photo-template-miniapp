from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class CandidateCreate(BaseModel):
    variant_text: str
    strategy: str

class EvolutionRunCreate(BaseModel):
    prompt_id: int
    base_version_id: int
    candidates: List[CandidateCreate]

class EvolutionRunResponse(BaseModel):
    id: int
    prompt_id: int
    base_version_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateResponse(BaseModel):
    id: int
    run_id: int
    variant_text: str
    strategy: str
    status: str
    promoted_version_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PromoteCandidateRequest(BaseModel):
    change_note: Optional[str] = None
    created_by: Optional[str] = "evolution_engine"

class EvaluationRecordCreate(BaseModel):
    asset_id: int
    prompt_version_id: int
    score: int
    feedback: Optional[str] = None

class EvaluationRecordResponse(BaseModel):
    id: int
    asset_id: int
    prompt_version_id: int
    score: int
    feedback: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
