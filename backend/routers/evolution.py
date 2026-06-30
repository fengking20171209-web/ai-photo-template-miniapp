from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from backend.database import SessionLocal
from backend.dependencies import get_db
from backend.models import PromptVersion
from backend.schemas.evolution import (
    EvolutionRunCreate, EvolutionRunResponse, CandidateResponse, CandidateCreate,
    PromoteCandidateRequest, EvaluationRecordCreate, EvaluationRecordResponse
)
from backend.schemas.workflow import PromptVersionResponse
from backend import crud_evolution

router = APIRouter(prefix="/prompt-evolution", tags=["evolution"])

# Mock Generator logic
def generate_mock_variants(base_text: str) -> List[CandidateCreate]:
    return [
        CandidateCreate(
            variant_text=base_text + " (make it more clear)",
            strategy="clarity"
        ),
        CandidateCreate(
            variant_text=base_text + " (use a poetic style)",
            strategy="style"
        ),
        CandidateCreate(
            variant_text=base_text + " (keep it extremely concise)",
            strategy="conciseness"
        )
    ]

@router.get("/base-version/{version_id}", response_model=PromptVersionResponse)
def get_base_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version

@router.post("/runs", response_model=EvolutionRunResponse)
def create_run(base_version_id: int, prompt_id: int = None, db: Session = Depends(get_db)):
    base_version = db.query(PromptVersion).filter(PromptVersion.id == base_version_id).first()
    if not base_version:
        raise HTTPException(status_code=404, detail="Base prompt version not found")
    
    actual_prompt_id = prompt_id or base_version.prompt_id

    if base_version.prompt_id != actual_prompt_id:
        raise HTTPException(status_code=400, detail="Base version does not belong to the given prompt_id")

    candidates_create = generate_mock_variants(base_version.content)
    
    run_create = EvolutionRunCreate(
        prompt_id=actual_prompt_id,
        base_version_id=base_version_id,
        candidates=candidates_create
    )
    db_run, _ = crud_evolution.create_evolution_run(db, run_create)
    return db_run

@router.get("/runs/{prompt_id}", response_model=List[EvolutionRunResponse])
def get_runs(prompt_id: int, db: Session = Depends(get_db)):
    return crud_evolution.get_evolution_runs(db, prompt_id)

@router.get("/runs/{run_id}/candidates", response_model=List[CandidateResponse])
def get_candidates(run_id: int, db: Session = Depends(get_db)):
    return crud_evolution.get_candidates(db, run_id)

@router.post("/candidates/{candidate_id}/promote", response_model=CandidateResponse)
def promote_candidate(candidate_id: int, req: PromoteCandidateRequest, db: Session = Depends(get_db)):
    candidate = crud_evolution.promote_candidate(db, candidate_id, req)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found or could not be promoted")
    return candidate

@router.post("/candidates/{candidate_id}/reject", response_model=CandidateResponse)
def reject_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = crud_evolution.reject_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/evaluations", response_model=EvaluationRecordResponse)
def create_evaluation(req: EvaluationRecordCreate, db: Session = Depends(get_db)):
    return crud_evolution.create_evaluation_record(db, req)

@router.get("/evaluations/asset/{asset_id}", response_model=List[EvaluationRecordResponse])
def get_evaluations_for_asset(asset_id: int, db: Session = Depends(get_db)):
    return crud_evolution.get_evaluation_records_for_asset(db, asset_id)
