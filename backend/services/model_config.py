"""Model configuration store.

Provides a small persisted config for image-generation providers and default
generation parameters, editable via the settings UI. API keys entered here take
precedence over environment variables; if left blank, the service falls back to
the corresponding .env value.

Stored at config/models.json (gitignored — may contain API keys).
"""
import json
import logging
import os
from copy import deepcopy
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "models.json"

# In-memory cache keyed by file mtime to avoid re-reading on every request.
_CACHE: dict | None = None
_CACHE_MTIME: float | None = None

# Default providers mirror the built-in integrations.
DEFAULTS = {
    "providers": [
        {
            "id": "sensenova",
            "name": "SenseNova U1",
            "provider_type": "sensenova",
            "base_url": "https://token.sensenova.cn/v1",
            "model": "sensenova-u1-fast",
            "api_key": "",
            "enabled": True,
            "capabilities": ["text2img"],
        },
        {
            "id": "agnes",
            "name": "Agnes Image 2.1 Flash",
            "provider_type": "agnes",
            "base_url": "https://apihub.agnes-ai.com/v1",
            "model": "agnes-image-2.1-flash",
            "api_key": "",
            "enabled": True,
            "capabilities": ["text2img", "img2img"],
        },
    ],
    "default_provider": "sensenova",
    "generation": {
        "temperature": 0.8,
        "max_tokens": 1024,
        "size": "",
        "n": 1,
        "stop": [],
    },
}

# Env var fallback per provider for the API key.
_ENV_KEY = {"sensenova": "SENSE_API_KEY", "agnes": "AGNES_API_KEY"}


def load_config() -> dict:
    """Load the stored config, falling back to defaults.

    Cached by file mtime so repeated calls within a request don't re-read disk.
    """
    global _CACHE, _CACHE_MTIME
    cfg = deepcopy(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            mtime = CONFIG_PATH.stat().st_mtime
            if _CACHE is not None and mtime == _CACHE_MTIME:
                return deepcopy(_CACHE)
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if isinstance(data.get("providers"), list) and data["providers"]:
                    cfg["providers"] = data["providers"]
                if data.get("default_provider"):
                    cfg["default_provider"] = data["default_provider"]
                if isinstance(data.get("generation"), dict):
                    cfg["generation"].update(data["generation"])
            _CACHE = deepcopy(cfg)
            _CACHE_MTIME = mtime
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to load %s, using defaults: %s", CONFIG_PATH.name, e)
    return cfg


def save_config(cfg: dict) -> None:
    """Persist the config to disk."""
    global _CACHE, _CACHE_MTIME
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    # Invalidate cache so the next load reflects the new file.
    _CACHE = None
    _CACHE_MTIME = None


def get_provider(provider_id: str) -> dict | None:
    for p in load_config()["providers"]:
        if p.get("id") == provider_id:
            return p
    return None


def resolve_api_key(provider_id: str) -> str:
    """API key for a provider: config value if set, else the .env fallback."""
    p = get_provider(provider_id)
    if p and (p.get("api_key") or "").strip():
        return p["api_key"].strip()
    env_name = _ENV_KEY.get(provider_id)
    return os.getenv(env_name, "") if env_name else ""


def resolve_base_url(provider_id: str, default: str) -> str:
    p = get_provider(provider_id)
    if p and (p.get("base_url") or "").strip():
        return p["base_url"].strip()
    return default


def resolve_model(provider_id: str, default: str) -> str:
    p = get_provider(provider_id)
    if p and (p.get("model") or "").strip():
        return p["model"].strip()
    return default


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}…{key[-4:]}"


def public_config() -> dict:
    """Config for the UI: API keys are masked, never returned in full."""
    cfg = deepcopy(load_config())
    for p in cfg["providers"]:
        raw = p.get("api_key") or ""
        env_name = _ENV_KEY.get(p.get("id"))
        env_key = os.getenv(env_name, "") if env_name else ""
        effective = raw or env_key
        p["has_key"] = bool(effective)
        p["key_preview"] = _mask_key(effective)
        p["key_source"] = "config" if raw else ("env" if env_key else "none")
        p.pop("api_key", None)
    return cfg
