"""Image generation endpoint."""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Union, List
from qcloud_cos import CosConfig, CosS3Client

from backend.dependencies import get_db
from backend.models import Image
from backend.services.sense_image import full_pipeline
from backend.services.agnes_image import full_pipeline as agnes_full_pipeline
from backend.services.local_storage import save_image_from_url
from backend.services.prompt_policy import build_image_prompt, build_diy_prompt

load_dotenv()
load_dotenv(".env.sub", override=True)

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

# COS client init
cos_cfg = CosConfig(
    Region=os.getenv("COS_REGION"),
    SecretId=os.getenv("COS_SUB_SECRET_ID", os.getenv("COS_SECRET_ID")),
    SecretKey=os.getenv("COS_SUB_SECRET_KEY", os.getenv("COS_SECRET_KEY")),
)
cos_client = CosS3Client(cos_cfg)
COS_BUCKET_GEN = os.getenv("COS_BUCKET_GEN", "")


def _load_template(template_id: str) -> dict:
    """Load a single template JSON file from disk."""
    filepath = TEMPLATES_DIR / f"{template_id}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class GenerateRequest(BaseModel):
    template_id: Optional[str] = Field(None, description="Template ID to load prompt from")
    prompt: Optional[str] = Field(None, min_length=1, max_length=2000, description="User prompt for image generation")
    background: Optional[str] = Field(None, max_length=600, description="DIY background/scene; overrides the template's locked scene")
    negative_prompt: Optional[str] = Field(None, max_length=1000, description="Negative prompt sent as a separate provider parameter (not inline)")
    size: Optional[str] = Field(None, description="Image size, e.g. 1920x1080")
    n: int = Field(1, ge=1, le=4, description="Number of images to generate")
    provider: Optional[str] = Field(None, description="Image provider: sensenova | agnes")
    image: Optional[Union[str, List[str]]] = Field(
        None,
        description="Image-to-image input: a public HTTPS URL or Data URI (data:image/...;base64,...), or a list. Agnes only.",
    )


class GenerateResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    template: Optional[dict] = None
    image_response: Optional[dict] = None
    error: Optional[str] = None


@router.get("/providers")
def list_providers():
    """List available image-generation providers and their capabilities.

    Lets the frontend build a model selector and know which providers are
    configured (have an API key) and which support image-to-image.
    """
    enable_real = os.getenv("ENABLE_REAL_IMAGE_API", "").lower() in ("true", "1", "yes")
    providers = [
        {
            "id": "sensenova",
            "name": "SenseNova U1",
            "model": os.getenv("SENSE_IMAGE_MODEL", "sensenova-u1-fast"),
            "capabilities": ["text2img"],
            "configured": bool(os.getenv("SENSE_API_KEY")),
        },
        {
            "id": "agnes",
            "name": "Agnes Image 2.1 Flash",
            "model": os.getenv("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash"),
            "capabilities": ["text2img", "img2img"],
            "configured": bool(os.getenv("AGNES_API_KEY")),
        },
    ]
    return {
        "providers": providers,
        "default": os.getenv("IMAGE_PROVIDER", "sensenova").lower(),
        "real_enabled": enable_real,
    }


@router.post("", response_model=GenerateResponse)
def generate_image(req: GenerateRequest, db: Session = Depends(get_db)):
    """Generate image from template or prompt using SenseTime API pipeline."""
    # COS is opt-in (PERSIST_TO_COS). Agnes and the local-persist path do not
    # need a COS bucket, so we no longer hard-fail when COS_BUCKET_GEN is unset.
    fail_reason: Optional[str] = None

    # Determine provider first because prompt policy has light provider-specific rules.
    provider = (req.provider or os.getenv("IMAGE_PROVIDER", "sensenova")).lower()
    if req.image:
        provider = "agnes"

    # Determine prompt source. DIY Prompt OS (default ON): the final prompt is
    # composed ONLY from user input + optional model identity. Legacy template
    # `prompt_blocks` (ancient beauty / 貂蝉 / classical archetypes) are NEVER
    # auto-injected. Set DIY_PROMPT_OS=false to restore the old template merge.
    import logging
    log = logging.getLogger(__name__)
    diy_mode = os.getenv("DIY_PROMPT_OS", "true").lower() in ("true", "1", "yes")
    injected_templates: list[str] = []
    template = None

    if diy_mode:
        if not req.prompt and not req.image:
            raise HTTPException(400, "DIY mode: a user prompt (or a reference image) is required; no template fallback.")
        user_prompt = build_diy_prompt(req.prompt, provider, background=req.background)
    else:
        # Legacy template-merge path (deprecated).
        if req.template_id:
            template = _load_template(req.template_id)
            injected_templates.append(req.template_id)
        if not template and not req.prompt:
            raise HTTPException(400, "Either template_id or prompt must be provided")
        user_prompt = build_image_prompt(template, req.prompt, provider, background=req.background)

    # --- Prompt Source Breakdown (debug) ---
    log.info(
        "Prompt Source Breakdown | mode=%s | user_input=%r | background=%r | model_identity=frontend-merged | injected_templates=%s",
        "DIY" if diy_mode else "legacy",
        (req.prompt or "")[:300],
        (req.background or "")[:150],
        injected_templates or "DISABLED",
    )
    # Hard guard: in DIY mode no template may ever be injected.
    if diy_mode and injected_templates:
        raise HTTPException(409, "Legacy template injection detected in DIY mode; generation blocked.")

    # Build frontend-compatible template summary (shared by both paths)
    template_summary = None
    if template:
        template_summary = {
            "template_id": template.get("template_id"),
            "category": template.get("category", ""),
            "title": template.get("title", ""),
            "style": template.get("style", ""),
            "ratio": template.get("ratio", ""),
            "face_lock": template.get("face_lock", False),
            "price": float(template.get("price", 0.0)) if template.get("price") is not None else 0.0,
            "is_free": bool(template.get("is_free", True)),
        }

    # Only call real paid API when explicitly enabled
    enable_real = os.getenv("ENABLE_REAL_IMAGE_API", "").lower() in ("true", "1", "yes")

    if enable_real:
        # Prefer an explicit size, otherwise derive from the template ratio.
        gen_size = req.size or (template.get("ratio") if template else None)
        # COS persistence is opt-in and requires a configured bucket.
        persist_cos = (
            os.getenv("PERSIST_TO_COS", "").lower() in ("true", "1", "yes")
            and bool(COS_BUCKET_GEN)
        )
        # Image-to-image is only supported by Agnes, so provider was resolved above.
        try:
            if provider == "agnes":
                result = agnes_full_pipeline(
                    user_prompt=user_prompt,
                    size=gen_size,
                    n=req.n,
                    image=req.image,
                    negative_prompt=req.negative_prompt,
                )
            else:
                provider = "sensenova"
                result = full_pipeline(
                    user_prompt=user_prompt,
                    cos_client=cos_client if persist_cos else None,
                    cos_bucket=COS_BUCKET_GEN if persist_cos else "",
                    size=gen_size,
                    n=req.n,
                    negative_prompt=req.negative_prompt,
                )
        except Exception as e:
            # Real API failed — log and fall back to mock so the UX never breaks,
            # but capture the reason so the frontend can tell the user why.
            fail_reason = str(e)
            import logging
            logging.getLogger(__name__).warning("Real image generation failed (provider=%s), falling back to mock: %s", provider, e)
        else:
            # Real generation succeeded
            display_url = result.get("display_url") or result["image_url"]
            stored_url = (
                f"cos://{COS_BUCKET_GEN}/{result['cos_key']}"
                if result.get("cos_key")
                else result["image_url"]
            )

            # Persist locally for a durable gallery (default on). Provider URLs
            # (e.g. SenseNova signed URLs) expire, so download once and serve
            # from /generated. Falls back to the direct URL on any failure.
            local_persist = os.getenv("LOCAL_PERSIST", "true").lower() in ("true", "1", "yes")
            if local_persist and not result.get("cos_key"):
                try:
                    local_path = save_image_from_url(result["image_url"])
                    display_url = local_path
                    stored_url = local_path
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning("Local persist failed, using direct URL: %s", e)

            img = Image(
                title=f"Generated: {user_prompt[:50]}",
                prompt=user_prompt,
                revised_prompt=result.get("revised_prompt", ""),
                image_url=stored_url,
                thumbnail_url=display_url,
                tags=["generated", provider],
                source=provider,
                source_id=result.get("cos_key") or result["image_url"],
            )
            db.add(img)
            db.commit()
            db.refresh(img)

            return GenerateResponse(
                status="completed",
                task_id=str(img.id),
                template=template_summary,
                image_response={
                    "image_urls": [display_url],
                    "raw": {"mode": "real", "provider": provider},
                },
            )

    # Mock / failed generation: DO NOT persist to the gallery (avoid clutter
    # from content-policy rejections and dev-mode mocks). The frontend shows
    # the reason instead of a fake result.
    raw = {"mode": "mock", "fallback": not enable_real}
    if fail_reason:
        # Real generation was attempted but failed (often a content-policy
        # rejection). Surface a short reason so the UI can inform the user.
        raw["fallback"] = True
        raw["reason"] = fail_reason[:300]
    return GenerateResponse(
        status="completed",
        task_id=None,
        template=template_summary,
        image_response={
            "image_urls": ["/placeholder.svg"],
            "raw": raw,
        },
    )
