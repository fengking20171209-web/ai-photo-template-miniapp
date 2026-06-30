from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.dependencies import get_db
from backend.crud import (
    create_prompt_draft,
    update_prompt_draft,
    publish_prompt_draft,
    discard_prompt_draft,
)
from backend.schemas.workflow import (
    PromptDraftCreate,
    PromptDraftUpdate,
    PublishDraftRequest,
    PromptDraftResponse,
    PromptVersionResponse
)
from backend.models import PromptDraft

router = APIRouter()

@router.post("/drafts", response_model=PromptDraftResponse)
def create_draft(draft_in: PromptDraftCreate, db: Session = Depends(get_db)):
    draft = create_prompt_draft(
        db=db,
        title=draft_in.title,
        content=draft_in.content,
        system_message=draft_in.system_message,
        parameters_json=draft_in.parameters_json,
        prompt_id=draft_in.prompt_id
    )
    return draft

@router.patch("/drafts/{draft_id}", response_model=PromptDraftResponse)
def update_draft(draft_id: int, draft_in: PromptDraftUpdate, db: Session = Depends(get_db)):
    draft = update_prompt_draft(
        db=db,
        draft_id=draft_id,
        title=draft_in.title,
        content=draft_in.content,
        system_message=draft_in.system_message,
        parameters_json=draft_in.parameters_json
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.post("/drafts/{draft_id}/publish", response_model=PromptVersionResponse)
def publish_draft(draft_id: int, req: PublishDraftRequest, db: Session = Depends(get_db)):
    version = publish_prompt_draft(
        db=db,
        draft_id=draft_id,
        change_note=req.change_note,
        created_by=req.created_by
    )
    if not version:
        raise HTTPException(status_code=400, detail="Cannot publish draft (not found or already published/discarded)")
    return version

@router.post("/drafts/{draft_id}/discard", response_model=PromptDraftResponse)
def discard_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = discard_prompt_draft(db=db, draft_id=draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.get("/drafts/{draft_id}", response_model=PromptDraftResponse)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(PromptDraft).filter(PromptDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft
