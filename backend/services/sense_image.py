"""SenseTime / SenseNova image generation service.

Uses the SenseNova OpenAI-compatible REST API (Bearer auth):
  - Base URL: https://token.sensenova.cn/v1
  - Chat (prompt optimization): POST /chat/completions  (model: sensenova-6.7-flash-lite)
  - Image generation:           POST /images/generations (model: sensenova-u1-fast)

Two-stage pipeline:
  1. optimize_prompt(): refine the Chinese prompt into a detailed English prompt
  2. generate_image(): generate the image and return its URL
"""
import logging
import os
import uuid

import requests
from dotenv import load_dotenv

from backend.services import model_config

logger = logging.getLogger(__name__)

load_dotenv()
load_dotenv(".env.sub", override=True)

# --- Config ---
# Normalise the base URL so it always ends with /v1 (the OpenAI-compatible root).
_raw_base = os.getenv("SENSE_API_BASE", "https://token.sensenova.cn/v1").rstrip("/")
if not _raw_base.endswith("/v1"):
    _raw_base = _raw_base + "/v1"
SENSE_API_BASE = _raw_base
SENSE_API_KEY = os.getenv("SENSE_API_KEY", "")
SENSE_CHAT_MODEL = os.getenv("SENSE_CHAT_MODEL", "sensenova-6.7-flash-lite")
SENSE_IMAGE_MODEL = os.getenv("SENSE_IMAGE_MODEL", "sensenova-u1-fast")
SENSE_IMAGE_SIZE = os.getenv("SENSE_IMAGE_SIZE", "2048x2048")

# Sizes accepted by the sensenova-u1-fast image model.
VALID_IMAGE_SIZES = {
    "1664x2496", "2496x1664", "1760x2368", "2368x1760", "1824x2272",
    "2272x1824", "2048x2048", "2752x1536", "1536x2752", "3072x1376",
    "1344x3136", "2560x720", "3072x864",
}

# Map common template aspect ratios to the closest supported size.
RATIO_TO_SIZE = {
    "1:1": "2048x2048",
    "4:5": "1824x2272",
    "5:4": "2272x1824",
    "3:4": "1824x2272",
    "4:3": "2272x1824",
    "2:3": "1664x2496",
    "3:2": "2496x1664",
    "9:16": "1536x2752",
    "16:9": "2752x1536",
}


def _auth_headers() -> dict:
    key = model_config.resolve_api_key("sensenova") or SENSE_API_KEY
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _base_url() -> str:
    return model_config.resolve_base_url("sensenova", SENSE_API_BASE)


def _image_model() -> str:
    return model_config.resolve_model("sensenova", SENSE_IMAGE_MODEL)


def normalize_size(size: str | None) -> str:
    """Resolve a requested size or aspect ratio to a supported image size."""
    if not size:
        # Fall back to the configured default size, then the module default.
        cfg_size = (model_config.load_config().get("generation", {}) or {}).get("size") or ""
        if cfg_size:
            size = cfg_size
        else:
            return SENSE_IMAGE_SIZE if SENSE_IMAGE_SIZE in VALID_IMAGE_SIZES else "2048x2048"
    if size in VALID_IMAGE_SIZES:
        return size
    if size in RATIO_TO_SIZE:
        return RATIO_TO_SIZE[size]
    return "2048x2048"


def optimize_prompt(user_prompt: str) -> str:
    """Refine the user's (Chinese) prompt into a detailed English image prompt.

    Note: sensenova-6.7-flash-lite is a reasoning model, so it needs a generous
    token budget for the answer to appear in `message.content` (the `reasoning`
    field is consumed first). Falls back to the original prompt on any issue.
    """
    payload = {
        "model": SENSE_CHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional fashion photography prompt engineer. "
                    "Translate the user's Chinese prompt into a detailed English prompt "
                    "for AI image generation. Keep it concise, descriptive and "
                    "photography-oriented. Include lighting, composition, style and mood. "
                    "Output only the prompt text, no explanations."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
    }
    try:
        resp = requests.post(
            f"{_base_url()}/chat/completions",
            headers=_auth_headers(),
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        message = resp.json()["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        return content or user_prompt
    except Exception as e:  # noqa: BLE001 - degrade gracefully
        logger.warning("Prompt optimization failed, using raw prompt: %s", e)
        return user_prompt


def generate_image(prompt: str, size: str | None = None, n: int = 1, negative_prompt: str | None = None) -> dict:
    """Generate image(s) via the OpenAI-compatible images endpoint.

    Returns dict with: image_url, revised_prompt, raw_response.
    Raises RuntimeError if no image URL can be obtained.
    """
    resolved_size = normalize_size(size)
    payload = {
        "model": _image_model(),
        "prompt": prompt,
        "n": max(1, min(int(n or 1), 4)),
        "size": resolved_size,
    }
    if negative_prompt and negative_prompt.strip():
        payload["negative_prompt"] = negative_prompt.strip()
    resp = requests.post(
        f"{_base_url()}/images/generations",
        headers=_auth_headers(),
        json=payload,
        timeout=180,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Image generation failed: {resp.status_code} {resp.text[:300]}")

    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"No image returned. Raw: {resp.text[:300]}")

    image_url = items[0].get("url") or items[0].get("image_url")
    if not image_url:
        raise RuntimeError(f"No image URL in response. Raw: {resp.text[:300]}")

    revised_prompt = items[0].get("revised_prompt") or prompt
    return {
        "image_url": image_url,
        "revised_prompt": revised_prompt,
        "raw_response": data,
    }


def download_and_upload(image_url: str, cos_client, cos_bucket: str) -> str:
    """Download an image and upload it to COS. Returns the COS key.

    Uses the same SSRF/size guards as local_storage (https + host allowlist,
    no redirects, streaming with a byte cap).
    """
    from datetime import datetime, timezone

    from backend.services.local_storage import _is_url_allowed, MAX_DOWNLOAD_BYTES

    if not _is_url_allowed(image_url):
        raise ValueError("Refusing to download image from disallowed URL (SSRF guard)")

    resp = requests.get(image_url, timeout=120, stream=True, allow_redirects=False)
    if 300 <= resp.status_code < 400:
        resp.close()
        raise ValueError(f"Refusing to follow redirect from image URL (status {resp.status_code})")
    resp.raise_for_status()

    chunks = []
    total = 0
    for chunk in resp.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_DOWNLOAD_BYTES:
            resp.close()
            raise ValueError(f"Image exceeds max size ({MAX_DOWNLOAD_BYTES} bytes)")
        chunks.append(chunk)
    content = b"".join(chunks)

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    file_id = uuid.uuid4().hex[:8]
    cos_key = f"gen/{today}/{file_id}.png"

    cos_client.put_object(
        Bucket=cos_bucket,
        Key=cos_key,
        Body=content,
        ContentType="image/png",
    )
    return cos_key


def full_pipeline(user_prompt: str, cos_client=None, cos_bucket: str = "", size: str | None = None, n: int = 1, negative_prompt: str | None = None) -> dict:
    """Run the full pipeline: optimize prompt -> generate image -> (optionally) persist to COS.

    Returns dict with:
      - image_url:   the source (SenseNova) image URL
      - revised_prompt
      - cos_key:     COS object key if upload succeeded, else None
      - display_url: URL the frontend should use (COS-served path if persisted,
                     otherwise the direct SenseNova URL)
    """
    logger.info("Image pipeline start: prompt=%r size=%r n=%r", user_prompt, size, n)
    # Prompt optimization is opt-in: template prompts are already detailed English
    # photography prompts, and the reasoning chat model adds latency. Enable with
    # OPTIMIZE_PROMPT=true for free-form / Chinese prompts.
    if os.getenv("OPTIMIZE_PROMPT", "").lower() in ("true", "1", "yes"):
        revised = optimize_prompt(user_prompt)
    else:
        revised = user_prompt
    result = generate_image(revised, size, n, negative_prompt=negative_prompt)
    source_url = result["image_url"]

    cos_key = None
    display_url = source_url
    if cos_client is not None and cos_bucket:
        try:
            cos_key = download_and_upload(source_url, cos_client, cos_bucket)
            display_url = f"/cos/image/{cos_key}"
        except Exception as e:  # noqa: BLE001 - persistence is best-effort
            logger.warning("COS upload failed, serving direct URL instead: %s", e)

    logger.info("Image pipeline done: cos_key=%s", cos_key)
    return {
        "image_url": source_url,
        "revised_prompt": result.get("revised_prompt") or revised,
        "cos_key": cos_key,
        "display_url": display_url,
    }
