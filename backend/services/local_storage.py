"""Local image persistence.

Generated images come back as remote URLs (e.g. SenseNova signed URLs that
expire in ~1h, or Agnes URLs). To keep a durable gallery for this local-first
app, we download the image once and store it under ``output/generated/`` where
it is served by FastAPI at ``/generated/...``.
"""
import ipaddress
import logging
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# output/generated/ at the project root (FastAPI mounts this at /generated).
GENERATED_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "generated"

# Defense-in-depth for downloading provider image URLs.
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_HOST_SUFFIXES = (
    "agnes-ai.com",
    "agnes-ai.space",
    "sensenova.cn",
    "sensecoreapi-oss.cn",
    "sensecoreapi.cn",
    "myqcloud.com",
    "googleapis.com",
)


def _is_url_allowed(url: str) -> bool:
    """Only allow https URLs to known provider hosts, and never private IPs (SSRF guard)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if not any(host == s or host.endswith("." + s) for s in ALLOWED_HOST_SUFFIXES):
        return False
    # Reject hosts that resolve to private/loopback/link-local addresses.
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except Exception:
        return False
    return True


def _guess_ext(content_type: str | None, url: str) -> str:
    if content_type:
        ct = content_type.lower()
        if "png" in ct:
            return ".png"
        if "jpeg" in ct or "jpg" in ct:
            return ".jpg"
        if "webp" in ct:
            return ".webp"
    lowered = url.lower()
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if ext in lowered:
            return ".jpg" if ext == ".jpeg" else ext
    return ".png"


def save_image_from_url(url: str, timeout: int = 120) -> str:
    """Download an image and store it locally.

    Returns the served path (e.g. ``/generated/2026/06/30/<uuid>.png``).
    Raises on network/IO errors so the caller can fall back to the direct URL.
    """
    if not _is_url_allowed(url):
        raise ValueError("Refusing to download image from disallowed URL (SSRF guard)")

    # Do not follow redirects: an allowed host could 30x-redirect to an
    # unvalidated/internal target and bypass the allowlist.
    resp = requests.get(url, timeout=timeout, stream=True, allow_redirects=False)
    if resp.status_code >= 300 and resp.status_code < 400:
        resp.close()
        raise ValueError(f"Refusing to follow redirect from image URL (status {resp.status_code})")
    resp.raise_for_status()

    # Enforce a max size while streaming to avoid unbounded memory/disk usage.
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

    today = datetime.now(timezone.utc)
    sub = today.strftime("%Y/%m/%d")
    ext = _guess_ext(resp.headers.get("Content-Type"), url)
    file_id = uuid.uuid4().hex
    rel_dir = GENERATED_DIR / sub
    rel_dir.mkdir(parents=True, exist_ok=True)
    file_path = rel_dir / f"{file_id}{ext}"
    file_path.write_bytes(content)

    served = f"/generated/{sub}/{file_id}{ext}"
    logger.info("Saved generated image locally: %s (%d bytes)", served, len(content))
    return served
