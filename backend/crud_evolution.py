import hashlib
from sqlalchemy.orm import Session
from backend.models import PromptEvolutionRun, PromptEvolutionCandidate, PromptEvaluationRecord, PromptVersion, Prompt
from backend.schemas.evolution import EvolutionRunCreate, PromoteCandidateRequest, EvaluationRecordCreate

def create_evolution_run(db: Session, run_create: EvolutionRunCreate):
    db_run = PromptEvolutionRun(
        prompt_id=run_create.prompt_id,
        base_version_id=run_create.base_version_id,
        status="completed" # Using mock generator, we can just complete it instantly
    )
    db.add(db_run)
    db.flush() # flush to get run_id

    candidates = []
    for c in run_create.candidates:
        db_candidate = PromptEvolutionCandidate(
            run_id=db_run.id,
            variant_text=c.variant_text,
            strategy=c.strategy,
            status="pending"
        )
        db.add(db_candidate)
        candidates.append(db_candidate)

    db.commit()
    db.refresh(db_run)
    return db_run, candidates

def get_evolution_runs(db: Session, prompt_id: int):
    return db.query(PromptEvolutionRun).filter(PromptEvolutionRun.prompt_id == prompt_id).order_by(PromptEvolutionRun.id.desc()).all()

def get_candidates(db: Session, run_id: int):
    return db.query(PromptEvolutionCandidate).filter(PromptEvolutionCandidate.run_id == run_id).all()

def promote_candidate(db: Session, candidate_id: int, req: PromoteCandidateRequest):
    candidate = db.query(PromptEvolutionCandidate).filter(PromptEvolutionCandidate.id == candidate_id).first()
    if not candidate:
        return None

    if candidate.status == "promoted":
        return candidate # already promoted

    run = db.query(PromptEvolutionRun).filter(PromptEvolutionRun.id == candidate.run_id).first()
    if not run:
        return None

    base_version = db.query(PromptVersion).filter(PromptVersion.id == run.base_version_id).first()
    if not base_version:
        return None

    prompt = db.query(Prompt).filter(Prompt.id == run.prompt_id).first()
    if not prompt:
        return None

    # Calculate content hash
    content_hash = hashlib.sha256(candidate.variant_text.encode('utf-8')).hexdigest()

    # Determine next version number
    latest_version = db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt.id).order_by(PromptVersion.version.desc()).first()
    next_version_num = (latest_version.version + 1) if latest_version else 1

    # Create new prompt version
    new_version = PromptVersion(
        prompt_id=prompt.id,
        version=next_version_num,
        content=candidate.variant_text,
        system_message=base_version.system_message,
        parameters_json=base_version.parameters_json,
        model_hint=base_version.model_hint,
        change_note=req.change_note or f"Promoted from evolution run {run.id}, candidate {candidate.id} (strategy: {candidate.strategy})",
        created_by=req.created_by,
        is_active=True,
        content_hash=content_hash
    )
    db.add(new_version)
    db.flush()

    prompt.current_version_id = new_version.id

    candidate.status = "promoted"
    candidate.promoted_version_id = new_version.id

    db.commit()
    db.refresh(candidate)
    return candidate

def reject_candidate(db: Session, candidate_id: int):
    candidate = db.query(PromptEvolutionCandidate).filter(PromptEvolutionCandidate.id == candidate_id).first()
    if not candidate:
        return None
    if candidate.status == "pending":
        candidate.status = "rejected"
        db.commit()
        db.refresh(candidate)
    return candidate

def create_evaluation_record(db: Session, record_create: EvaluationRecordCreate):
    record = PromptEvaluationRecord(
        asset_id=record_create.asset_id,
        prompt_version_id=record_create.prompt_version_id,
        score=record_create.score,
        feedback=record_create.feedback
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_evaluation_records_for_asset(db: Session, asset_id: int):
    return db.query(PromptEvaluationRecord).filter(PromptEvaluationRecord.asset_id == asset_id).order_by(PromptEvaluationRecord.id.desc()).all()
