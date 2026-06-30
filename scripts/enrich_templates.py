#!/usr/bin/env python3
"""Enrich template JSON files with auto-generated tags.

Scans templates/*.json and generates `tags` array based on
category, style, scene, and clothing fields.
"""

import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# Common tag keywords mapped from categories and styles
CATEGORY_TAGS = {
    "古风美女": ["古风", "美女", "写真", "传统", "汉服"],
    "职业形象": ["职业", "形象", "商务", "正装", "职场"],
    "形象分析": ["形象", "分析", "气质", "风格"],
    "漫画角色": ["漫画", "角色", "二次元", "卡通"],
    "产品海报": ["产品", "海报", "商业", "广告"],
    "模特大赛": ["模特", "时尚", "T台", "大赛"],
    "新中式概念": ["新中式", "概念", "国潮", "现代"],
    "肚兜现代时装": ["肚兜", "现代", "时装", "性感"],
    "SIUF 2026 内衣秀": ["内衣", "SIUF", "秀场", "时尚"],
    "人像写真": ["人像", "写真", "肖像", "摄影"],
    "幻系插画": ["幻系", "插画", "幻想", "艺术"],
}


def extract_tags(data: dict) -> list[str]:
    """Extract tags from template data."""
    tags = set()

    # Category-based tags
    category = data.get("category", "")
    if category in CATEGORY_TAGS:
        tags.update(CATEGORY_TAGS[category])

    # Style tag
    style = data.get("style", "")
    if style:
        tags.add(style)

    # Scene keywords (split by common delimiters)
    scene = data.get("scene", "")
    if scene:
        # Extract meaningful phrases (2-4 chars) from scene
        for phrase in scene.replace("，", ",").replace("、", ",").split(","):
            phrase = phrase.strip()
            if 2 <= len(phrase) <= 8:
                tags.add(phrase)

    # Clothing keywords
    clothing = data.get("clothing", "")
    if clothing:
        for phrase in clothing.replace("，", ",").replace("、", ",").split(","):
            phrase = phrase.strip()
            if 2 <= len(phrase) <= 8:
                tags.add(phrase)

    # Title keywords
    title = data.get("title", "")
    if title and len(title) <= 6:
        tags.add(title)

    return sorted(list(tags))


def main():
    if not TEMPLATES_DIR.exists():
        print(f"Templates directory not found: {TEMPLATES_DIR}")
        return

    json_files = sorted(TEMPLATES_DIR.glob("*.json"))
    success = 0
    skipped = 0
    failed = 0

    for f in json_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            # Skip if tags already exist and are non-empty
            if data.get("tags"):
                skipped += 1
                continue

            tags = extract_tags(data)
            data["tags"] = tags

            with open(f, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")

            success += 1
            print(f"[OK] {f.name}: {len(tags)} tags")
        except Exception as e:
            failed += 1
            print(f"[ERR] {f.name}: {e}")

    print(f"\nDone: {success} enriched, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
