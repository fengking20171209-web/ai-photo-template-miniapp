import hashlib
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Prompt, PromptVersion, PromptDraft, Task, TaskChain, TaskChainEdge

def _compute_hash(content: str, system_message: str, model_hint: str) -> str:
    """Compute a hash for prompt content to ensure uniqueness."""
    data = f"{content or ''}|{system_message or ''}|{model_hint or ''}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Prompts
def create_prompt(db: Session, name: str, category: str = None, description: str = None) -> Prompt:
    db_prompt = Prompt(name=name, category=category, description=description)
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def create_prompt_version(
    db: Session, 
    prompt_id: int, 
    content: str, 
    model_hint: str = None, 
    system_message: str = None, 
    parameters_json: Dict = None, 
    change_note: str = None,
    created_by: str = None
) -> PromptVersion:
    # Get current max version
    max_version = db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.version.desc()).first()
    next_version = 1 if not max_version else max_version.version + 1
    
    content_hash = _compute_hash(content, system_message, model_hint)
    
    # Check if hash already exists
    existing = db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id, PromptVersion.content_hash == content_hash).first()
    if existing:
        return existing
        
    db_version = PromptVersion(
        prompt_id=prompt_id,
        version=next_version,
        content=content,
        model_hint=model_hint,
        system_message=system_message,
        parameters_json=parameters_json,
        change_note=change_note,
        created_by=created_by,
        content_hash=content_hash
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    
    # Update current_version_id
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        prompt.current_version_id = db_version.id
        db.commit()
        
    return db_version

def get_prompt_current_version(db: Session, prompt_id: int) -> Optional[PromptVersion]:
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt and prompt.current_version_id:
        return db.query(PromptVersion).filter(PromptVersion.id == prompt.current_version_id).first()
    return None

def list_prompt_versions(db: Session, prompt_id: int) -> List[PromptVersion]:
    return db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.version.desc()).all()

def rollback_prompt_version(db: Session, prompt_id: int, version: int) -> Optional[PromptVersion]:
    db_version = db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id, PromptVersion.version == version).first()
    if db_version:
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if prompt:
            prompt.current_version_id = db_version.id
            db.commit()
            return db_version
    return None

# Tasks
def create_task(
    db: Session,
    title: str,
    task_type: str,
    input_json: Dict = None,
    prompt_version_id: int = None,
    parent_task_id: int = None,
    chain_id: int = None
) -> Task:
    db_task = Task(
        title=title,
        task_type=task_type,
        status="pending",
        input_json=input_json,
        prompt_version_id=prompt_version_id,
        parent_task_id=parent_task_id,
        chain_id=chain_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task_status(db: Session, task_id: int, status: str, output_json: Dict = None, error_message: str = None) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = status
        if output_json is not None:
            task.output_json = output_json
        if error_message is not None:
            task.error_message = error_message
        db.commit()
        db.refresh(task)
    return task

# Task Chains
def create_task_chain(db: Session, name: str, description: str = None) -> TaskChain:
    chain = TaskChain(name=name, description=description, status="created")
    db.add(chain)
    db.commit()
    db.refresh(chain)
    return chain

def append_task_to_chain(db: Session, chain_id: int, from_task_id: int, to_task_id: int, edge_type: str = "sequential") -> TaskChainEdge:
    edge = TaskChainEdge(
        chain_id=chain_id,
        from_task_id=from_task_id,
        to_task_id=to_task_id,
        edge_type=edge_type
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge

def get_task_chain_graph(db: Session, chain_id: int) -> Dict[str, Any]:
    chain = db.query(TaskChain).filter(TaskChain.id == chain_id).first()
    if not chain:
        return None
    
    tasks = db.query(Task).filter(Task.chain_id == chain_id).all()
    edges = db.query(TaskChainEdge).filter(TaskChainEdge.chain_id == chain_id).all()
    
    return {
        "chain": chain,
        "tasks": tasks,
        "edges": edges
    }

# Prompt Drafts
def create_prompt_draft(
    db: Session,
    title: str,
    content: str,
    system_message: str = None,
    parameters_json: Dict = None,
    prompt_id: int = None
) -> PromptDraft:
    draft = PromptDraft(
        prompt_id=prompt_id,
        title=title,
        content=content,
        system_message=system_message,
        parameters_json=parameters_json,
        status="draft"
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

def update_prompt_draft(
    db: Session,
    draft_id: int,
    title: str = None,
    content: str = None,
    system_message: str = None,
    parameters_json: Dict = None
) -> Optional[PromptDraft]:
    draft = db.query(PromptDraft).filter(PromptDraft.id == draft_id).first()
    if not draft:
        return None
    if title is not None:
        draft.title = title
    if content is not None:
        draft.content = content
    if system_message is not None:
        draft.system_message = system_message
    if parameters_json is not None:
        draft.parameters_json = parameters_json
    db.commit()
    db.refresh(draft)
    return draft

def discard_prompt_draft(db: Session, draft_id: int) -> Optional[PromptDraft]:
    draft = db.query(PromptDraft).filter(PromptDraft.id == draft_id).first()
    if draft:
        draft.status = "discarded"
        db.commit()
        db.refresh(draft)
    return draft

def publish_prompt_draft(
    db: Session,
    draft_id: int,
    change_note: str = None,
    created_by: str = None
) -> Optional[PromptVersion]:
    draft = db.query(PromptDraft).filter(PromptDraft.id == draft_id).first()
    if not draft or draft.status != "draft":
        return None
        
    try:
        # 1. Create prompt if prompt_id is None
        prompt_id = draft.prompt_id
        if not prompt_id:
            # Check if a prompt with the same title exists
            existing_prompt = db.query(Prompt).filter(Prompt.name == draft.title).first()
            if existing_prompt:
                prompt_id = existing_prompt.id
            else:
                new_prompt = Prompt(name=draft.title)
                db.add(new_prompt)
                db.flush() # get id without committing
                prompt_id = new_prompt.id
                draft.prompt_id = prompt_id

        # 2. Check hash to avoid duplicates
        content_hash = _compute_hash(draft.content, draft.system_message, None)
        existing_version = db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.content_hash == content_hash
        ).first()

        db_version = None
        if existing_version:
            db_version = existing_version
            # Ensure it is active
            if not db_version.is_active:
                db_version.is_active = True
                db.flush()
        else:
            # Get max version
            max_version = db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.version.desc()).first()
            next_version = 1 if not max_version else max_version.version + 1
            
            db_version = PromptVersion(
                prompt_id=prompt_id,
                version=next_version,
                content=draft.content,
                model_hint=None,
                system_message=draft.system_message,
                parameters_json=draft.parameters_json,
                change_note=change_note,
                created_by=created_by,
                content_hash=content_hash
            )
            db.add(db_version)
            db.flush()

        # 3. Update current_version_id
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if prompt:
            prompt.current_version_id = db_version.id

        # 4. Update draft status
        draft.status = "published"
        
        db.commit()
        db.refresh(db_version)
        return db_version
    except Exception as e:
        db.rollback()
        raise e
