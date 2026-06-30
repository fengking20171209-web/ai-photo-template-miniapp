"""Model & generation configuration endpoints (for the settings UI).

- GET  /api/config/models  → current config with API keys masked
- PUT  /api/config/models  → update providers / default / generation params
"""
import ipaddress
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.services import model_config

router = APIRouter()


def require_local(request: Request) -> None:
    """Allow config mutations only from loopback clients.

    Defense-in-depth: even if the server is later bound to 0.0.0.0, the
    config endpoints (which store API keys and outbound base URLs) stay
    restricted to the local machine.
    """
    client = request.client.host if request.client else None
    try:
        is_loopback = client is not None and ipaddress.ip_address(client).is_loopback
    except ValueError:
        is_loopback = client in ("localhost", "::1")
    if not is_loopback:
        raise HTTPException(status_code=403, detail="Config changes are restricted to localhost")


def _validate_base_url(url: str) -> Optional[str]:
    """Return an error message if base_url is unsafe, else None.

    base_url is used for server-side outbound requests carrying API keys, so
    only allow https and reject hosts resolving to private/loopback addresses
    (prevents redirecting the backend to internal/attacker hosts to leak keys).
    """
    if not url:
        return None  # empty handled elsewhere
    try:
        parsed = urlparse(url)
    except Exception:
        return "invalid base_url"
    if parsed.scheme != "https" or not parsed.hostname:
        return "base_url must be https"
    try:
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return "base_url host is not allowed"
    except Exception:
        return "base_url host could not be resolved"
    return None


class ProviderIn(BaseModel):
    id: str
    name: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None  # blank/omitted → keep existing stored key
    enabled: Optional[bool] = True
    capabilities: Optional[List[str]] = None


class GenerationIn(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    size: Optional[str] = None
    n: Optional[int] = None
    stop: Optional[List[str]] = None


class ConfigIn(BaseModel):
    providers: Optional[List[ProviderIn]] = None
    default_provider: Optional[str] = None
    generation: Optional[GenerationIn] = None


@router.get("/config/models")
def get_models_config() -> Dict[str, Any]:
    return model_config.public_config()


@router.put("/config/models")
def update_models_config(payload: ConfigIn, _: None = Depends(require_local)) -> Dict[str, Any]:
    current = model_config.load_config()
    existing_keys = {p.get("id"): (p.get("api_key") or "") for p in current["providers"]}

    if payload.providers is not None:
        merged: List[dict] = []
        for p in payload.providers:
            base_url = (p.base_url or "").strip()
            err = _validate_base_url(base_url)
            if err:
                return JSONResponse(status_code=400, content={"error": f"provider '{p.id}': {err}"})
            # Preserve the stored key unless a new non-empty one is supplied.
            new_key = (p.api_key or "").strip()
            api_key = new_key if new_key else existing_keys.get(p.id, "")
            merged.append({
                "id": p.id,
                "name": p.name or p.id,
                "provider_type": p.provider_type or p.id,
                "base_url": base_url,
                "model": (p.model or "").strip(),
                "api_key": api_key,
                "enabled": bool(p.enabled),
                "capabilities": p.capabilities or [],
            })
        current["providers"] = merged

    if payload.default_provider:
        current["default_provider"] = payload.default_provider

    if payload.generation is not None:
        gen = current.get("generation", {})
        for field, value in payload.generation.model_dump(exclude_none=True).items():
            gen[field] = value
        current["generation"] = gen

    model_config.save_config(current)
    return model_config.public_config()
