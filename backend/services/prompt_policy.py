"""Prompt policy for image generation.

This module keeps model-facing prompt composition in one place so templates,
free-form user input, and provider-specific quality rules stay consistent.
"""
from __future__ import annotations

from typing import Any


PROMPT_BLOCK_ORDER = (
    "subject",
    "face",
    "clothing",
    "scene",
    "lighting",
    "camera",
    "quality",
    "commercial_use",
)

# Providers that accept inline "Avoid:" negative phrasing in the positive prompt.
# Current image APIs (agnes, sensenova U1) do NOT — adding it triggers their
# content filters — so this stays empty until a provider supports it.
SUPPORTS_INLINE_NEGATIVE: set[str] = set()


# ---------------------------------------------------------------------------
# DIY Prompt OS
# ---------------------------------------------------------------------------
# The studio runs in a pure user-driven mode: the final prompt is composed
# ONLY from user input (scene/character/outfit/pose/lighting tags + free text)
# plus the optional selected model identity. NO legacy template archetypes
# (ancient beauty / 貂蝉 / classical idol presets) are auto-injected.
DIY_BASE_DIRECTIVE = (
    "pure user-driven composition, no predefined style archetypes, "
    "no historical beauty presets, modern cinematic realism, "
    "high fidelity subject consistency"
)


def build_diy_prompt(
    user_prompt: str | None,
    provider: str,
    background: str | None = None,
) -> str:
    """Compose a prompt purely from user input (DIY Prompt OS).

    Strict layering (highest priority first):
      1. user input (scene/character/outfit/pose/lighting + model identity,
         already merged by the caller into ``user_prompt``)
      2. user scene/background
      3. DIY base directive (anti-archetype, modern realism)
      4. technical quality rules
    No template ``prompt_blocks`` are ever injected here.
    """
    provider = (provider or "").lower()
    sections: list[str] = []

    cleaned_user_prompt = _clean_text(user_prompt)
    if cleaned_user_prompt:
        sections.append(cleaned_user_prompt)

    cleaned_background = _clean_text(background)
    if cleaned_background:
        sections.append(f"Scene / background: {cleaned_background}")

    sections.append(DIY_BASE_DIRECTIVE)
    sections.append(_diy_quality_rules(provider))

    return "\n\n".join(section for section in sections if section).strip()


def _diy_quality_rules(provider: str) -> str:
    base = (
        "Technical quality: coherent anatomy, natural body proportions, realistic skin texture, "
        "sharp focus, high detail, no visible text, no watermark, no logo artifacts."
    )
    if provider == "agnes":
        return base + " Follow the user's prompt literally; do not substitute any default aesthetic."
    if provider == "sensenova":
        return base + " Keep concise English photography phrasing; do not add unrequested style."
    return base


def build_image_prompt(
    template: dict[str, Any] | None,
    user_prompt: str | None,
    provider: str,
    background: str | None = None,
) -> str:
    """Build the final prompt sent to an image model.

    Background/scene is a user-controlled (DIY) dimension: when ``background``
    is supplied it overrides the template's locked ``scene`` block, so picking a
    template no longer freezes the backdrop. Template fields still provide
    subject/clothing/lighting/camera/quality structure; policy rules provide
    stable model behavior.
    """
    provider = (provider or "").lower()
    sections: list[str] = []

    cleaned_user_prompt = _clean_text(user_prompt)
    if cleaned_user_prompt:
        sections.append(f"User creative request: {cleaned_user_prompt}")

    cleaned_background = _clean_text(background)
    if cleaned_background:
        sections.append(
            f"Background / scene (use this, override any template scene): {cleaned_background}"
        )

    if template:
        # When the user picks a DIY background, drop the template's own scene
        # block so the backdrop is not locked by the template.
        template_prompt = _build_template_prompt(template, include_scene=not cleaned_background)
        if template_prompt:
            sections.append(f"Template direction: {template_prompt}")

        style = _clean_text(template.get("style"))
        ratio = _clean_text(template.get("ratio"))
        if style or ratio:
            sections.append("Visual format: " + ", ".join(x for x in [style, _ratio_instruction(ratio)] if x))

        if template.get("face_lock") is True:
            face_strength = _read_face_strength(template)
            sections.append(
                "Identity preservation: preserve the user's real facial identity, face shape, "
                f"facial proportions, skin tone and gaze; avoid changing the person. Face strength target: {face_strength:.2f}."
            )

    sections.append(_quality_rules(provider))

    # Inline "Avoid:" negatives are only safe for providers that support a
    # negative prompt. The current OpenAI-compatible image APIs (agnes,
    # sensenova) treat the whole prompt as positive text, so injecting words
    # like "nudity"/"vulgar" both trips their content filters
    # (content_policy_violation) and is counter-productive. Skip for them.
    if provider in SUPPORTS_INLINE_NEGATIVE:
        negative = _negative_rules(template)
        if negative:
            sections.append(f"Avoid: {negative}")

    return "\n\n".join(section for section in sections if section).strip()


def _build_template_prompt(template: dict[str, Any], include_scene: bool = True) -> str:
    blocks = template.get("prompt_blocks")
    parts: list[str] = []
    if isinstance(blocks, dict):
        for key in PROMPT_BLOCK_ORDER:
            if key == "scene" and not include_scene:
                continue
            value = _clean_text(blocks.get(key))
            if value:
                parts.append(value)

    if not parts:
        fallback_keys = ("scene", "clothing") if include_scene else ("clothing",)
        for key in fallback_keys:
            value = _clean_text(template.get(key))
            if value:
                parts.append(value)

    return "。".join(parts)


def _quality_rules(provider: str) -> str:
    base = (
        "Quality rules: professional commercial portrait photography, coherent anatomy, natural body proportions, "
        "realistic skin texture, clean styling, polished composition, premium editorial lighting, high detail, "
        "no visible text, no watermark, no logo artifacts. Keep clothing complete and tasteful."
    )
    if provider == "agnes":
        return base + " Follow the prompt literally and keep the result suitable for a refined AI photo studio product."
    if provider == "sensenova":
        return base + " Prefer concise English photography phrasing if the provider rewrites the prompt."
    return base


def _negative_rules(template: dict[str, Any] | None) -> str:
    defaults = [
        "low quality",
        "blurred face",
        "distorted facial features",
        "deformed hands",
        "extra fingers",
        "unnatural limbs",
        "over-smoothed skin",
        "plastic skin",
        "exaggerated body proportions",
        "nudity",
        "vulgar styling",
        "watermark",
        "text artifacts",
    ]
    if template:
        custom = template.get("negative_prompt")
        if isinstance(custom, list):
            defaults.extend(str(item).strip() for item in custom if str(item).strip())
    return ", ".join(dict.fromkeys(defaults))


def _ratio_instruction(ratio: str | None) -> str:
    if not ratio:
        return ""
    mapping = {
        "1:1": "square composition",
        "4:5": "vertical portrait composition, 4:5 aspect ratio",
        "3:4": "vertical portrait composition, 3:4 aspect ratio",
        "2:3": "full vertical portrait composition, 2:3 aspect ratio",
        "9:16": "mobile vertical composition, 9:16 aspect ratio",
        "16:9": "wide cinematic composition, 16:9 aspect ratio",
    }
    return mapping.get(ratio, f"aspect ratio {ratio}")


def _read_face_strength(template: dict[str, Any]) -> float:
    options = template.get("options")
    if isinstance(options, dict):
        value = options.get("face_strength")
        if isinstance(value, (int, float)):
            return max(0.0, min(float(value), 1.0))
    return 0.78


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())
