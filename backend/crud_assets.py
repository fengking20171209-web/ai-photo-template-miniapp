from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from backend.models import Asset, Task
from backend.schemas.assets import AssetCreate, AssetUpdate

def create_asset(db: Session, asset_in: AssetCreate) -> Asset:
    # Validation for task_id / source
    task_chain_id = None
    prompt_version_id = None
    
    if asset_in.task_id:
        task = db.query(Task).filter(Task.id == asset_in.task_id).first()
        if not task:
            raise ValueError(f"Task {asset_in.task_id} not found")
        task_chain_id = task.chain_id
        prompt_version_id = task.prompt_version_id
    elif asset_in.source == "uploaded":
        if not asset_in.metadata_json:
            raise ValueError("metadata_json is required when source is uploaded and task_id is not provided")
    else:
        raise ValueError("task_id is required unless source is 'uploaded'")

    db_asset = Asset(
        **asset_in.model_dump(),
        task_chain_id=task_chain_id,
        prompt_version_id=prompt_version_id
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id, Asset.is_deleted == False).first()

def get_assets(  
    db: Session,  
    skip: int = 0,  
    limit: int = 20,  
    asset_type: Optional[str] = None,  
    source: Optional[str] = None,  
    is_favorite: Optional[bool] = None,  
    is_deleted: Optional[bool] = False,  
    sort_by: Optional[str] = "created_at",  
    sort_order: Optional[str] = "desc",  
    recent_days: Optional[int] = None  
) -> Tuple[List[Asset], int]:  
    query = db.query(Asset)  
    if is_deleted is not None:  
        query = query.filter(Asset.is_deleted == is_deleted)  
    if asset_type:  
        query = query.filter(Asset.asset_type == asset_type)  
    if source:  
        query = query.filter(Asset.source == source)  
    if is_favorite is not None:  
        query = query.filter(Asset.is_favorite == is_favorite)  
    if recent_days is not None:  
        from datetime import datetime, timedelta, timezone  
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=recent_days)  
        query = query.filter(Asset.created_at >= cutoff_date)  
    total = query.count()  
    order_col = getattr(Asset, sort_by, Asset.created_at)  
    if sort_order == "asc":  
        from sqlalchemy import asc  
        query = query.order_by(asc(order_col))  
    else:  
        query = query.order_by(desc(order_col))  
    items = query.offset(skip).limit(limit).all()  
    return items, total

def get_assets_by_task(db: Session, task_id: int) -> List[Asset]:
    return db.query(Asset).filter(Asset.task_id == task_id, Asset.is_deleted == False).order_by(desc(Asset.created_at)).all()

def toggle_favorite(db: Session, asset_id: int, is_favorite: bool) -> Optional[Asset]:
    asset = get_asset(db, asset_id)
    if not asset:
        return None
    asset.is_favorite = is_favorite
    db.commit()
    db.refresh(asset)
    return asset

def soft_delete_asset(db: Session, asset_id: int) -> bool:
    asset = get_asset(db, asset_id)
    if not asset:
        return False
    asset.is_deleted = True
    asset.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True

def restore_asset(db: Session, asset_id: int) -> bool:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_deleted == True).first()
    if not asset:
        return False
    asset.is_deleted = False
    asset.deleted_at = None
    db.commit()
    return True

def update_asset(db: Session, asset_id: int, asset_in: AssetUpdate) -> Optional[Asset]:
    asset = get_asset(db, asset_id)
    if not asset:
        return None
    
    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)
        
    db.commit()
    db.refresh(asset)
    return asset
