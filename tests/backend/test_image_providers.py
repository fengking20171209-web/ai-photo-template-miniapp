"""Tests for image-generation providers, gallery URL resolution and endpoints.

These tests avoid real network calls — they cover the pure helpers (size
normalization, URL resolution) and the discovery/validation endpoints.
"""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import agnes_image, sense_image
from backend.routers.cos_serve import _resolve_image_urls

client = TestClient(app)


# --- Size normalization ---------------------------------------------------

def test_agnes_normalize_size_ratio_mapping():
    assert agnes_image.normalize_size("4:5") == "1024x1280"
    assert agnes_image.normalize_size("16:9") == "1365x768"


def test_agnes_normalize_size_passthrough_and_default():
    assert agnes_image.normalize_size("1024x768") == "1024x768"
    # Unknown ratio falls back to the configured default.
    assert agnes_image.normalize_size("weird") == agnes_image.AGNES_IMAGE_SIZE


def test_sense_normalize_size_valid_and_ratio():
    assert sense_image.normalize_size("2048x2048") == "2048x2048"
    assert sense_image.normalize_size("4:5") == "1824x2272"
    # Unsupported size resolves to a valid default.
    assert sense_image.normalize_size("999x999") in sense_image.VALID_IMAGE_SIZES


# --- Gallery URL resolution ------------------------------------------------

def _img(**kw):
    base = dict(source="agnes", thumbnail_url=None, image_url=None, source_id=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_resolve_local_persisted_url():
    img = _img(thumbnail_url="/generated/2026/06/30/abc.png", image_url="/generated/2026/06/30/abc.png")
    assert _resolve_image_urls(img) == (
        "/generated/2026/06/30/abc.png",
        "/generated/2026/06/30/abc.png",
    )


def test_resolve_direct_http_url():
    img = _img(thumbnail_url="https://cdn.example.com/x.png")
    image_url, thumb = _resolve_image_urls(img)
    assert image_url == "https://cdn.example.com/x.png"
    assert thumb == "https://cdn.example.com/x.png"


def test_resolve_mock_placeholder():
    img = _img(source="mock", thumbnail_url=None)
    assert _resolve_image_urls(img) == ("/placeholder.svg", "/placeholder.svg")


def test_resolve_legacy_cos_key():
    img = _img(thumbnail_url=None, image_url=None, source_id="gen/2026/abc.png")
    assert _resolve_image_urls(img) == ("/cos/image/gen/2026/abc.png", "/cos/image/gen/2026/abc.png")


def test_resolve_legacy_http_source_id():
    img = _img(thumbnail_url=None, image_url=None, source_id="https://signed.example.com/x.png")
    image_url, _ = _resolve_image_urls(img)
    assert image_url == "https://signed.example.com/x.png"


# --- Endpoints -------------------------------------------------------------

def test_providers_endpoint():
    resp = client.get("/generate/providers")
    assert resp.status_code == 200
    data = resp.json()
    ids = {p["id"] for p in data["providers"]}
    assert {"sensenova", "agnes"} <= ids
    agnes = next(p for p in data["providers"] if p["id"] == "agnes")
    assert "img2img" in agnes["capabilities"]


def test_chat_requires_messages():
    # No messages -> 400 (or 503 if no key configured). Never a 5xx crash.
    resp = client.post("/chat", json={})
    assert resp.status_code in (400, 503)


def test_generate_requires_template_or_prompt():
    resp = client.post("/generate", json={})
    assert resp.status_code == 400


def test_generate_surfaces_failure_reason(monkeypatch):
    """When the real provider fails, the mock fallback must carry the reason."""
    # Other test modules drop_all on the shared engine; ensure tables exist
    # before this endpoint writes the mock Image row.
    from backend.database import Base, engine
    Base.metadata.create_all(bind=engine)

    monkeypatch.setenv("ENABLE_REAL_IMAGE_API", "true")

    def boom(**kwargs):
        raise RuntimeError("content_policy_violation: blocked")

    monkeypatch.setattr("backend.routers.image_gen.agnes_full_pipeline", boom)
    resp = client.post("/generate", json={"prompt": "a calm scene", "provider": "agnes"})
    assert resp.status_code == 200
    raw = resp.json()["image_response"]["raw"]
    assert raw["mode"] == "mock"
    assert raw["fallback"] is True
    assert "content_policy_violation" in raw["reason"]


def test_config_rejects_non_https_base_url():
    """PUT must reject http/private base_url (SSRF/key-leak guard)."""
    from backend.routers.config import require_local

    app.dependency_overrides[require_local] = lambda: None
    try:
        resp = client.put(
            "/api/config/models",
            json={"providers": [{"id": "agnes", "base_url": "http://169.254.169.254/v1"}]},
        )
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.pop(require_local, None)


def test_config_put_blocked_for_non_local():
    """Config mutation from a non-loopback client is rejected."""
    resp = client.put("/api/config/models", json={"default_provider": "agnes"})
    assert resp.status_code == 403


# --- DIY background overrides locked template scene ------------------------

def test_background_overrides_template_scene():
    from backend.services.prompt_policy import build_image_prompt

    template = {"prompt_blocks": {
        "subject": "a portrait of a woman",
        "scene": "inside a locked palace hall",
        "clothing": "a red dress",
    }}
    out = build_image_prompt(template, None, "agnes", background="on a sunny beach at sunset")
    assert "sunny beach" in out          # DIY background used
    assert "locked palace hall" not in out  # template scene dropped
    assert "red dress" in out            # non-scene template blocks kept


def test_template_scene_kept_without_background():
    from backend.services.prompt_policy import build_image_prompt

    template = {"prompt_blocks": {"scene": "inside a palace hall"}}
    out = build_image_prompt(template, None, "agnes")
    assert "palace hall" in out          # legacy behavior preserved


# --- DIY Prompt OS: 纯用户驱动，绝不注入模板 -------------------------------

def test_build_diy_prompt_no_template_injection():
    from backend.services.prompt_policy import build_diy_prompt, DIY_BASE_DIRECTIVE

    out = build_diy_prompt("a woman on a city rooftop, neon night", "agnes", background="neon street")
    # 用户输入与背景在内
    assert "city rooftop" in out
    assert "neon street" in out
    # DIY 基线指令注入（反风格档案）
    assert DIY_BASE_DIRECTIVE in out
    # 绝不出现古风/历史美人等模板漂移词
    low = out.lower()
    for drift in ("ancient", "diaochan", "classical", "hanfu", "palace hall"):
        assert drift not in low


def test_build_diy_prompt_empty_user_still_neutral():
    from backend.services.prompt_policy import build_diy_prompt, DIY_BASE_DIRECTIVE

    out = build_diy_prompt("", "sensenova")
    assert DIY_BASE_DIRECTIVE in out      # 仍给中性基线
    assert "ancient" not in out.lower()


def test_build_diy_prompt_anti_archetype_directive():
    from backend.services.prompt_policy import DIY_BASE_DIRECTIVE

    # 基线明确禁止预设风格档案 / 历史美人
    assert "no predefined style archetypes" in DIY_BASE_DIRECTIVE
    assert "no historical beauty presets" in DIY_BASE_DIRECTIVE
