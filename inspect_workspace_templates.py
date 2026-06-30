import json
from pathlib import Path

root = Path(r"D:\Projects\ai-photo-template-miniapp")
templates = sorted((root / "templates").glob("*.json"))
print("template_count", len(templates))
for p in templates[:20]:
    print(p.name)

if templates:
    sample = templates[0]
    print("\n== sample ==", sample.name)
    data = json.loads(sample.read_text(encoding="utf-8"))
    keys = ["template_id", "category", "title", "style", "ratio", "face_lock", "scene", "clothing", "tags"]
    for k in keys:
        if k in data:
            print(k, repr(data[k])[:300])
    print("prompt_blocks_keys", list((data.get("prompt_blocks") or {}).keys()))
