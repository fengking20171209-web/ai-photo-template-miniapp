"""COS image proxy - serves images from COS buckets via signed URLs/proxy."""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from qcloud_cos import CosConfig, CosS3Client

from backend.dependencies import get_db
from backend.models import Image
from backend.services.local_storage import GENERATED_DIR

load_dotenv()
load_dotenv(".env.sub", override=True)

router = APIRouter()

cos_cfg = CosConfig(
    Region=os.getenv("COS_REGION"),
    SecretId=os.getenv("COS_SUB_SECRET_ID", os.getenv("COS_SECRET_ID")),
    SecretKey=os.getenv("COS_SUB_SECRET_KEY", os.getenv("COS_SECRET_KEY")),
)
cos_client = CosS3Client(cos_cfg)
COS_BUCKET_GEN = os.getenv("COS_BUCKET_GEN", "")
COS_BUCKET_REF = os.getenv("COS_BUCKET_REF", "")


@router.get("/cos/image/{cos_key:path}")
def proxy_cos_image(cos_key: str):
    """Proxy an image from COS. Returns the image bytes with correct content type."""
    # Determine which bucket based on path prefix
    if cos_key.startswith("ref/"):
        bucket = COS_BUCKET_REF
    elif cos_key.startswith("gen/"):
        bucket = COS_BUCKET_GEN
    else:
        # Default to gen bucket
        bucket = COS_BUCKET_GEN

    if not bucket:
        raise HTTPException(500, "COS bucket not configured")

    try:
        # Generate a signed URL (valid for 1 hour)
        url = cos_client.get_object_url(
            Bucket=bucket,
            Key=cos_key,
            Expires=3600,
        )
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch image from COS: {e}")


def _servable(value: str) -> bool:
    """Whether a stored URL can be served to the client as-is."""
    return value.startswith(("/generated/", "/placeholder", "/cos/image/", "http://", "https://"))


def _resolve_image_urls(img):
    """Resolve (image_url, thumbnail_url) for an Image record across all sources.

    Handles: locally-persisted images (/generated/...), direct provider URLs,
    legacy COS keys, and mock placeholders.
    """
    if img.source == "mock":
        u = img.thumbnail_url or "/placeholder.svg"
        return u, u
    # Prefer a directly-servable stored URL (local path, http(s), placeholder).
    for cand in (img.thumbnail_url, img.image_url):
        if cand and _servable(cand):
            return cand, cand
    # source_id may be a direct URL (legacy) or a COS object key.
    sid = img.source_id or ""
    if sid.startswith(("http://", "https://")):
        return sid, sid
    if sid:
        return f"/cos/image/{sid}", f"/cos/image/{sid}"
    return None, None


@router.get("/images/recent")
def list_recent_images(limit: int = 20, db: Session = Depends(get_db)):
    """List recently generated images. Mock/failed placeholders are excluded
    so content-policy failures and dev mocks don't pollute the gallery."""
    limit = max(1, min(limit, 100))
    items = (
        db.query(Image)
        .filter(Image.source != "mock")
        .filter(Image.thumbnail_url != "/placeholder.svg")
        .order_by(Image.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for img in items:
        image_url, thumbnail_url = _resolve_image_urls(img)
        results.append({
            "id": img.id,
            "title": img.title,
            "prompt": img.prompt,
            "revised_prompt": img.revised_prompt,
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "tags": img.tags or [],
            "source": img.source,
        })
    return {"total": len(results), "items": results}


@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    """Get a single image record by ID."""
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

    image_url, thumbnail_url = _resolve_image_urls(img)

    return {
        "id": img.id,
        "title": img.title,
        "prompt": img.prompt,
        "revised_prompt": img.revised_prompt,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "created_at": img.created_at.isoformat() if img.created_at else None,
        "tags": img.tags or [],
        "source": img.source,
    }


def _delete_local_files(img) -> None:
    """Remove locally-persisted /generated files for an image record.

    Only touches files under GENERATED_DIR (path-traversal guarded); COS/http/
    mock entries have no local file and are skipped.
    """
    base = GENERATED_DIR.resolve()
    seen = set()
    for url in (img.image_url, img.thumbnail_url):
        if not url or not url.startswith("/generated/"):
            continue
        rel = url[len("/generated/"):]
        if rel in seen:
            continue
        seen.add(rel)
        try:
            p = (GENERATED_DIR / rel).resolve()
            if (p == base or base in p.parents) and p.is_file():
                p.unlink()
        except Exception:
            pass


@router.post("/images/bulk-delete")
def bulk_delete_images(payload: dict, db: Session = Depends(get_db)):
    """Delete multiple image records (and their local files) by id list.
    Body: {"ids": [1,2,3]}."""
    ids = payload.get("ids") if isinstance(payload, dict) else None
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail="ids (non-empty list) required")
    ids = [int(i) for i in ids[:500] if str(i).isdigit() or isinstance(i, int)]
    rows = db.query(Image).filter(Image.id.in_(ids)).all()
    for img in rows:
        _delete_local_files(img)
    for img in rows:
        db.delete(img)
    db.commit()
    return {"deleted": len(rows), "ids": ids}


@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image record (and its local file) by ID."""
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    _delete_local_files(img)
    db.delete(img)
    db.commit()
    return {"deleted": True, "id": image_id}
