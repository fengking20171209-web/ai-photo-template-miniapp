"""Model-persona library endpoints.

Stores reusable characters (a bound reference face + identity/negative prompt
blocks) for identity-consistent generation. No LoRA/training involved.
"""
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models import ModelPersona

router = APIRouter()

# Reference images are base64 data URIs; cap to keep the DB/payloads sane.
MAX_REF_CHARS = 8 * 1024 * 1024  # ~8MB of base64


class ModelIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    reference_image: Optional[str] = None
    identity_prompt: Optional[str] = ""
    negative_prompt: Optional[str] = ""
    tags: Optional[List[str]] = None


def _serialize(m: ModelPersona) -> Dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "reference_image": m.reference_image or "",
        "identity_prompt": m.identity_prompt or "",
        "negative_prompt": m.negative_prompt or "",
        "tags": m.tags or [],
        "usage_count": m.usage_count or 0,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _validate_ref(ref: Optional[str]) -> None:
    if ref and len(ref) > MAX_REF_CHARS:
        raise HTTPException(status_code=413, detail="Reference image too large")


@router.get("/models")
def list_models(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rows = db.query(ModelPersona).order_by(ModelPersona.created_at.desc()).all()
    return {"models": [_serialize(m) for m in rows]}


@router.post("/models")
def create_model(payload: ModelIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _validate_ref(payload.reference_image)
    m = ModelPersona(
        id="m_" + uuid.uuid4().hex[:12],
        name=payload.name.strip(),
        reference_image=payload.reference_image or "",
        identity_prompt=(payload.identity_prompt or "").strip(),
        negative_prompt=(payload.negative_prompt or "").strip(),
        tags=payload.tags or [],
        usage_count=0,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.put("/models/{model_id}")
def update_model(model_id: str, payload: ModelIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _validate_ref(payload.reference_image)
    m = db.query(ModelPersona).filter(ModelPersona.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    m.name = payload.name.strip()
    if payload.reference_image is not None:
        m.reference_image = payload.reference_image
    m.identity_prompt = (payload.identity_prompt or "").strip()
    m.negative_prompt = (payload.negative_prompt or "").strip()
    m.tags = payload.tags or []
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.delete("/models/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    m = db.query(ModelPersona).filter(ModelPersona.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(m)
    db.commit()
    return {"ok": True}


@router.post("/models/{model_id}/use")
def use_model(model_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    m = db.query(ModelPersona).filter(ModelPersona.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    m.usage_count = (m.usage_count or 0) + 1
    db.commit()
    db.refresh(m)
    return _serialize(m)
