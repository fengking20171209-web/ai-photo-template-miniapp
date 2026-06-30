"""Lightweight analytics event recording.

The frontend posts url-encoded events (event_type, template_id, query,
category, session_id) to power trending/usage features. Parsed manually to
avoid a python-multipart dependency.
"""
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models import UserEvent

router = APIRouter()

ALLOWED_EVENTS = {"click", "generate", "batch_generate", "search", "view"}


@router.post("/analytics/event")
async def record_event(request: Request, db: Session = Depends(get_db)):
    raw = (await request.body()).decode("utf-8", "ignore")
    data = {k: v[0] for k, v in parse_qs(raw).items()}
    event_type = (data.get("event_type") or "").strip()[:50]
    if not event_type:
        return {"ok": False, "error": "event_type required"}
    ev = UserEvent(
        event_type=event_type,
        template_id=(data.get("template_id") or None),
        query=(data.get("query") or None),
        category=(data.get("category") or None),
        session_id=(data.get("session_id") or None),
    )
    db.add(ev)
    db.commit()
    return {"ok": True}
