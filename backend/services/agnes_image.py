"""Agnes AI image generation service.

Uses the Agnes Image OpenAI-style REST API (Bearer auth):
  - Base URL: https://apihub.agnes-ai.com/v1
  - Image generation: POST /images/generations  (model: agnes-image-2.1-flash)

Notes (per Agnes docs):
  - `model`, `prompt` and `size` are required for text-to-image.
  - To get a URL result, put `"response_format": "url"` inside `extra_body`
    (it must NOT be placed at the top level).
  - The generated image URL is at `data[0].url`.
"""
import logging
import os

import requests
from dotenv import load_dotenv

from backend.services import model_config

logger = logging.getLogger(__name__)

load_dotenv()
load_dotenv(".env.sub", override=True)

_raw_base = os.getenv("AGNES_API_BASE", "https://apihub.agnes-ai.com/v1").rstrip("/")
if not _raw_base.endswith("/v1"):
    _raw_base = _raw_base + "/v1"
AGNES_API_BASE = _raw_base
AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")
AGNES_IMAGE_MODEL = os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash")
AGNES_IMAGE_SIZE = os.getenv("AGNES_IMAGE_SIZE", "1024x1024")

# Agnes accepts flexible custom sizes; map common template ratios to sensible ones.
RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "4:5": "1024x1280",
    "5:4": "1280x1024",
    "3:4": "1024x1365",
    "4:3": "1365x1024",
    "2:3": "1024x1536",
    "3:2": "1536x1024",
    "9:16": "768x1365",
    "16:9": "1365x768",
}


def _auth_headers() -> dict:
    key = model_config.resolve_api_key("agnes") or AGNES_API_KEY
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _base_url() -> str:
    return model_config.resolve_base_url("agnes", AGNES_API_BASE)


def _image_model() -> str:
    return model_config.resolve_model("agnes", AGNES_IMAGE_MODEL)


def normalize_size(size: str | None) -> str:
    """Resolve a requested size or aspect ratio to an output size string."""
    if not size:
        # Fall back to the configured default size, then the module default.
        cfg_size = (model_config.load_config().get("generation", {}) or {}).get("size") or ""
        if cfg_size:
            size = cfg_size  # continue through ratio/size resolution below
        else:
            return AGNES_IMAGE_SIZE
    # Already a WxH size.
    if "x" in size and size.replace("x", "").isdigit():
        return size
    if size in RATIO_TO_SIZE:
        return RATIO_TO_SIZE[size]
    return AGNES_IMAGE_SIZE


def generate_image(prompt: str, size: str | None = None, n: int = 1, image=None, negative_prompt: str | None = None) -> dict:
    """Generate (text-to-image) or transform (image-to-image) via Agnes.

    Args:
        prompt: text instruction.
        size:   output size or aspect ratio.
        n:      ignored by Agnes (single image), kept for signature parity.
        image:  optional input image(s) for image-to-image. A public HTTPS URL
                or a Data URI (data:image/...;base64,...), or a list of them.

    Returns dict with: image_url, revised_prompt, raw_response.
    Raises RuntimeError if no image URL can be obtained.
    """
    if not (model_config.resolve_api_key("agnes") or AGNES_API_KEY):
        raise RuntimeError("AGNES_API_KEY is not configured")

    extra_body: dict = {"response_format": "url"}
    if image:
        # Agnes expects image-to-image inputs inside extra_body.image as an array.
        extra_body["image"] = [image] if isinstance(image, str) else list(image)
    if negative_prompt and negative_prompt.strip():
        # Pass negatives as a separate parameter (NOT inline) to avoid tripping
        # the positive-prompt content filter.
        extra_body["negative_prompt"] = negative_prompt.strip()

    payload = {
        "model": _image_model(),
        "prompt": prompt,
        "size": normalize_size(size),
        "extra_body": extra_body,
    }
    resp = requests.post(
        f"{_base_url()}/images/generations",
        headers=_auth_headers(),
        json=payload,
        timeout=360,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Agnes image generation failed: {resp.status_code} {resp.text[:300]}")

    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise RuntimeError(f"No image returned. Raw: {resp.text[:300]}")

    image_url = items[0].get("url")
    if not image_url:
        raise RuntimeError(f"No image URL in response. Raw: {resp.text[:300]}")

    revised_prompt = items[0].get("revised_prompt") or prompt
    return {
        "image_url": image_url,
        "revised_prompt": revised_prompt,
        "raw_response": data,
    }


def full_pipeline(user_prompt: str, size: str | None = None, n: int = 1, image=None, negative_prompt: str | None = None) -> dict:
    """Generate or transform an image with Agnes.

    Returns dict with image_url, revised_prompt, cos_key (always None here) and
    display_url (the direct Agnes URL), matching the shape used by image_gen.
    """
    logger.info("Agnes image pipeline start: size=%r img2img=%s", size, bool(image))
    result = generate_image(user_prompt, size, n, image=image, negative_prompt=negative_prompt)
    return {
        "image_url": result["image_url"],
        "revised_prompt": result.get("revised_prompt") or user_prompt,
        "cos_key": None,
        "display_url": result["image_url"],
    }
