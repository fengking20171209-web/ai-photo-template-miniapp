"""Template catalog API - serves template JSON files from the templates/ directory."""

import hashlib
import json
import math
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, HTTPException
from sqlalchemy import func

from backend.schemas.search import TemplateSearchParams, TemplateSearchResponse, TemplateSearchItem
from backend.database import SessionLocal
from backend.models import UserEvent

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _templates_dir_hash() -> str:
    """Return a hash of all template file mtimes to detect changes."""
    hasher = hashlib.md5()
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        hasher.update(f"{f.name}:{f.stat().st_mtime}".encode())
    return hasher.hexdigest()


@lru_cache(maxsize=1)
def _load_all_templates_cached(_dir_hash: str) -> list[dict]:
    """Load all template JSON files from disk (cached until files change)."""
    templates = []
    if not TEMPLATES_DIR.exists():
        return templates
    for f in sorted(TEMPLATES_DIR.glob("*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            templates.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return templates


def _load_all_templates() -> list[dict]:
    """Return cached templates, reloading only when directory contents change."""
    return _load_all_templates_cached(_templates_dir_hash())


@router.get("/templates")
def list_templates():
    """Return a list of all available templates."""
    items = _load_all_templates()
    return {
        "total": len(items),
        "items": [
            {
                "template_id": t.get("template_id"),
                "category": t.get("category", ""),
                "title": t.get("title", ""),
                "style": t.get("style", ""),
                "ratio": t.get("ratio", ""),
                "face_lock": t.get("face_lock", False),
                "scene": t.get("scene", ""),
                "clothing": t.get("clothing", ""),
            }
            for t in items
        ],
    }


@router.get("/templates/search", response_model=TemplateSearchResponse)
def search_templates(
    q: str | None = None,
    category: str | None = None,
    is_free: bool | None = None,
    page: int = 1,
    limit: int = 20,
    sort: str = "title",
):
    """Search templates with keyword filter, category filter, free filter, sorting and pagination."""
    params = TemplateSearchParams(q=q, category=category, page=page, limit=limit, sort=sort)
    items = _load_all_templates()

    # Filter by keyword (title, template_id, style, scene, clothing, tags)
    if params.q:
        keyword = params.q.lower()
        items = [
            t for t in items
            if (
                keyword in (t.get("title") or "").lower()
                or keyword in (t.get("template_id") or "").lower()
                or keyword in (t.get("style") or "").lower()
                or keyword in (t.get("scene") or "").lower()
                or keyword in (t.get("clothing") or "").lower()
                or any(keyword in tag.lower() for tag in (t.get("tags") or []))
            )
        ]

    # Filter by category
    if params.category:
        items = [t for t in items if (t.get("category") or "") == params.category]

    # is_free filter is ignored in open-source version (all templates are free)
    # Parameter kept for backward compatibility

    # Sort
    sort_field = params.sort if params.sort in ("title", "template_id", "category") else "title"
    items.sort(key=lambda t: (t.get(sort_field) or "").lower())

    total = len(items)
    offset = (params.page - 1) * params.limit
    paginated = items[offset:offset + params.limit]

    pages = math.ceil(total / params.limit) if total > 0 else 1

    return TemplateSearchResponse(
        total=total,
        page=params.page,
        pages=pages,
        items=[
            TemplateSearchItem(
                template_id=t.get("template_id", ""),
                category=t.get("category", ""),
                title=t.get("title", ""),
                style=t.get("style", ""),
                ratio=t.get("ratio", ""),
                face_lock=t.get("face_lock", False),
                scene=t.get("scene", ""),
                clothing=t.get("clothing", ""),
                tags=t.get("tags", []),
                description=t.get("description"),
            )
            for t in paginated
        ],
    )


@router.get("/templates/recommended")
def recommended_templates(limit: int = 8):
    """Return a curated list of recommended templates.

    Prioritizes free templates and ensures category diversity.
    """
    items = _load_all_templates()
    # All templates are included in open-source version
    free_items = items
    seen_cats = set()
    result = []
    for t in free_items:
        cat = t.get("category", "")
        if cat not in seen_cats or len(result) < limit:
            result.append(t)
            seen_cats.add(cat)
        if len(result) >= limit:
            break
    return {
        "total": len(result),
        "items": [
            {
                "template_id": t.get("template_id"),
                "category": t.get("category", ""),
                "title": t.get("title", ""),
                "style": t.get("style", ""),
                "ratio": t.get("ratio", ""),
                "face_lock": t.get("face_lock", False),
                "scene": t.get("scene", ""),
                "clothing": t.get("clothing", ""),
            }
            for t in result
        ],
    }


@router.get("/templates/recent")
def get_recent_templates(days: int = 30, limit: int = 8):
    """Alias for /templates/recently-used."""
    return recently_used_templates(days=days, limit=limit)


@router.get("/templates/recently-used")
def recently_used_templates(days: int = 30, limit: int = 8):
    """Return templates the user has recently interacted with.

    Based on click, generate, and batch_generate events.
    """
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        # Get distinct template_ids ordered by most recent event
        results = (
            db.query(
                UserEvent.template_id,
                func.max(UserEvent.created_at).label("last_used"),
            )
            .filter(
                UserEvent.event_type.in_(["click", "generate", "batch_generate"]),
                UserEvent.created_at >= since,
                UserEvent.template_id.isnot(None),
            )
            .group_by(UserEvent.template_id)
            .order_by(func.max(UserEvent.created_at).desc())
            .limit(limit)
            .all()
        )

        # Map to full template summaries
        all_templates = {t.get("template_id"): t for t in _load_all_templates()}
        items = []
        for r in results:
            t = all_templates.get(r.template_id)
            if t:
                items.append({
                    "template_id": t.get("template_id"),
                    "category": t.get("category", ""),
                    "title": t.get("title", ""),
                    "style": t.get("style", ""),
                    "ratio": t.get("ratio", ""),
                    "face_lock": t.get("face_lock", False),
                    "scene": t.get("scene", ""),
                    "clothing": t.get("clothing", ""),
                    "last_used": r.last_used.isoformat() if r.last_used else None,
                })

        return {"total": len(items), "items": items}
    finally:
        db.close()


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    """Return full detail for a single template."""
    items = _load_all_templates()
    for t in items:
        if t.get("template_id") == template_id:
            return t
    raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")


@router.post("/analytics/event")
def track_event(
    event_type: str = Form(...),
    template_id: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """Track a user interaction event for analytics."""
    db = SessionLocal()
    try:
        event = UserEvent(
            event_type=event_type,
            template_id=template_id,
            query=query,
            category=category,
            session_id=session_id,
        )
        db.add(event)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/analytics/popular")
def popular_templates(days: int = 7, limit: int = 10):
    """Return the most popular templates based on user events.

    Aggregates click, favorite, and batch_generate events over the last N days.
    """
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        results = (
            db.query(
                UserEvent.template_id,
                func.count(UserEvent.id).label("score"),
            )
            .filter(
                UserEvent.event_type.in_(["click", "favorite", "batch_generate"]),
                UserEvent.created_at >= since,
                UserEvent.template_id.isnot(None),
            )
            .group_by(UserEvent.template_id)
            .order_by(func.count(UserEvent.id).desc())
            .limit(limit)
            .all()
        )
        return {
            "days": days,
            "items": [
                {"template_id": r.template_id, "score": r.score}
                for r in results
            ],
        }
    finally:
        db.close()
