from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.dependencies import get_db
from backend.crud import create_task, update_task_status, get_task_chain_graph
from backend.schemas.workflow import TaskSubmit, TaskResponse
from backend.models import Task

router = APIRouter()

@router.post("/", response_model=TaskResponse)
def submit_task(task_in: TaskSubmit, db: Session = Depends(get_db)):
    task = create_task(
        db=db,
        title=task_in.title,
        task_type=task_in.task_type,
        input_json=task_in.input_json,
        prompt_version_id=task_in.prompt_version_id,
        parent_task_id=task_in.parent_task_id,
        chain_id=task_in.chain_id
    )
    return task

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/chain/{chain_id}")
def get_chain(chain_id: int, db: Session = Depends(get_db)):
    graph = get_task_chain_graph(db=db, chain_id=chain_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Format the graph response
    chain = graph["chain"]
    return {
        "chain": {
            "id": chain.id,
            "name": chain.name,
            "status": chain.status
        },
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "task_type": t.task_type
            } for t in graph["tasks"]
        ],
        "edges": [
            {
                "id": e.id,
                "from_task_id": e.from_task_id,
                "to_task_id": e.to_task_id,
                "edge_type": e.edge_type
            } for e in graph["edges"]
        ]
    }
