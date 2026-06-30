from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.database import SessionLocal
from backend import crud_assets
from backend.schemas.assets import AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
from backend.models import Task

router = APIRouter(prefix="/api/assets", tags=["assets"])
tasks_router = APIRouter(prefix="/api/tasks", tags=["tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    try:
        return crud_assets.create_asset(db, asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=AssetListResponse)
def get_assets(  
    page: int = Query(1, ge=1),  
    size: int = Query(20, ge=1, le=100),  
    asset_type: Optional[str] = None,  
    source: Optional[str] = None,  
    is_favorite: Optional[bool] = None,  
    is_deleted: Optional[bool] = False,  
    sort_by: Optional[str] = "created_at",  
    sort_order: Optional[str] = "desc",  
    recent_days: Optional[int] = None,  
    db: Session = Depends(get_db)  
):  
    skip = (page - 1) * size  
    items, total = crud_assets.get_assets(  
        db, skip=skip, limit=size, asset_type=asset_type, source=source, is_favorite=is_favorite,  
        is_deleted=is_deleted, sort_by=sort_by, sort_order=sort_order, recent_days=recent_days  
    )  
    return AssetListResponse(items=items, total=total, page=page, size=size)

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = crud_assets.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset_in: AssetUpdate, db: Session = Depends(get_db)):
    asset = crud_assets.update_asset(db, asset_id, asset_in)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/{asset_id}/favorite", response_model=AssetResponse)
def favorite_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = crud_assets.toggle_favorite(db, asset_id, True)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.delete("/{asset_id}/favorite", response_model=AssetResponse)
def unfavorite_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = crud_assets.toggle_favorite(db, asset_id, False)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    success = crud_assets.soft_delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")

@router.post("/{asset_id}/restore", response_model=AssetResponse)
def restore_asset(asset_id: int, db: Session = Depends(get_db)):
    success = crud_assets.restore_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Deleted asset not found")
    return crud_assets.get_asset(db, asset_id)

@tasks_router.get("/{task_id}/assets", response_model=List[AssetResponse])
def get_task_assets(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return crud_assets.get_assets_by_task(db, task_id)
