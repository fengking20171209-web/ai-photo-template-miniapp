#!/usr/bin/env python3
"""Remove price and is_free fields from all template JSON files."""
import json
from pathlib import Path


def main() -> None:
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    files = sorted(template_dir.glob("*.json"))
    updated = 0
    skipped = 0

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        if "price" in data:
            del data["price"]
            changed = True
        if "is_free" in data:
            del data["is_free"]
            changed = True
        if changed:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            updated += 1
        else:
            skipped += 1

    print(f"Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
