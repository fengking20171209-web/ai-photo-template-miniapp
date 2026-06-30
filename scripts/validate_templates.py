#!/usr/bin/env python3
"""Validate all template JSON files against the project schema."""
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = ["template_id", "category", "title", "version", "ratio", "face_lock", "style", "scene", "clothing", "prompt_blocks", "options", "negative_prompt"]
PROMPT_BLOCK_KEYS = ["subject", "face", "clothing", "scene", "lighting", "camera", "quality", "commercial_use"]


def validate_template(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON decode error: {e}"]

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")

    template_id = data.get("template_id", "")
    if template_id and template_id != path.stem:
        errors.append(f"template_id '{template_id}' does not match filename '{path.stem}'")

    prompt_blocks = data.get("prompt_blocks", {})
    if isinstance(prompt_blocks, dict):
        for key in PROMPT_BLOCK_KEYS:
            if key not in prompt_blocks:
                errors.append(f"missing prompt_blocks.{key}")
    else:
        errors.append("prompt_blocks must be an object")

    if "price" in data:
        errors.append("unexpected field: price (should be removed for open-source)")
    if "is_free" in data:
        errors.append("unexpected field: is_free (should be removed for open-source)")

    return errors


def main() -> int:
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    files = sorted(template_dir.glob("*.json"))
    total = len(files)
    failed = 0

    for f in files:
        errors = validate_template(f)
        if errors:
            failed += 1
            print(f"FAIL {f.name}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {f.name}")

    print(f"\n{'='*50}")
    print(f"Total: {total}, Passed: {total - failed}, Failed: {failed}")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
