import json
import os
import sys
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {
    "古风美女",
    "职业形象",
    "形象分析",
    "漫画角色",
    "产品海报",
    "模特大赛",
}

ALLOWED_QUALITY = {"draft", "standard", "high"}
DEFAULT_PROJECT_ROOT = Path(r"D:\Projects\ai-photo-template-miniapp")

REQUIRED_TOP = [
    "template_id",
    "category",
    "title",
    "version",
    "ratio",
    "face_lock",
    "style",
    "scene",
    "clothing",
    "prompt_blocks",
    "options",
    "negative_prompt",
]

REQUIRED_BLOCKS = [
    "subject",
    "face",
    "clothing",
    "scene",
    "lighting",
    "camera",
    "quality",
    "commercial_use",
]


def main() -> None:
    if len(sys.argv) < 2:
        fail("Missing command")

    command = sys.argv[1]
    params = read_params()
    root = resolve_project_root(params)

    if command == "list_templates":
        emit({"templates": list_templates(root)})
    elif command == "smoke_test":
        emit(smoke_test(root, params.get("template_id") or ""))
    elif command == "check_image_env":
        emit(check_image_env(root))
    elif command == "generate_catalog":
        emit(generate_catalog(root))
    else:
        fail(f"Unknown command: {command}")


def read_params() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def resolve_project_root(params: dict[str, Any]) -> Path:
    candidate = (
        params.get("project_root")
        or os.environ.get("AI_PHOTO_TEMPLATE_PROJECT_ROOT")
        or find_project_root(Path.cwd())
        or DEFAULT_PROJECT_ROOT
    )
    root = Path(candidate).resolve()
    if not (root / "templates").is_dir():
        fail(f"Project root does not contain templates/: {root}")
    return root


def find_project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "templates").is_dir() and (candidate / "src").is_dir():
            return candidate
    return None


def load_template(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_template_files(root: Path) -> list[Path]:
    return sorted((root / "templates").glob("*.json"))


def list_templates(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in iter_template_files(root):
        template = load_template(path)
        rows.append(
            {
                "template_id": template.get("template_id"),
                "category": template.get("category"),
                "title": template.get("title"),
                "ratio": template.get("ratio"),
                "style": template.get("style"),
                "quality": (template.get("options") or {}).get("quality"),
                "face_strength": (template.get("options") or {}).get("face_strength"),
            }
        )
    return rows


def smoke_test(root: Path, template_id: str) -> dict[str, Any]:
    files = iter_template_files(root)
    if template_id:
        files = [path for path in files if path.stem == template_id]
        if not files:
            fail(f"Template not found: {template_id}")

    output_dir = root / "output" / "test-runs"
    output_dir.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    results = []

    for path in files:
        template = load_template(path)
        errors = validate_template(path, template, seen_ids)
        task = build_mock_task(template, errors)
        (output_dir / f"{template.get('template_id', path.stem)}.json").write_text(
            json.dumps(task, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        results.append(
            {
                "file": path.name,
                "template_id": template.get("template_id"),
                "status": task["status"],
                "errors": len(errors),
                "prompt_chars": len(task["image_request"]["request_body"]["prompt"]),
            }
        )

    summary = {
        "total": len(results),
        "passed": len([item for item in results if item["status"] == "completed"]),
        "failed": len([item for item in results if item["status"] != "completed"]),
        "results": results,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def validate_template(path: Path, template: dict[str, Any], seen_ids: set[str]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP:
        if key not in template:
            errors.append(f"missing {key}")

    template_id = template.get("template_id")
    if template_id != path.stem:
        errors.append("template_id must match file name")

    if isinstance(template_id, str):
        if template_id in seen_ids:
            errors.append(f"duplicate template_id: {template_id}")
        seen_ids.add(template_id)

    if template.get("category") not in ALLOWED_CATEGORIES:
        errors.append(f"unsupported category: {template.get('category')}")

    blocks = template.get("prompt_blocks")
    if not isinstance(blocks, dict):
        errors.append("prompt_blocks must be an object")
    else:
        for key in REQUIRED_BLOCKS:
            if not isinstance(blocks.get(key), str) or not blocks.get(key, "").strip():
                errors.append(f"missing prompt_blocks.{key}")

    options = template.get("options")
    if not isinstance(options, dict):
        errors.append("options must be an object")
    else:
        if options.get("quality") not in ALLOWED_QUALITY:
            errors.append(f"unsupported quality: {options.get('quality')}")
        face_strength = options.get("face_strength")
        if not isinstance(face_strength, (int, float)) or not 0 <= face_strength <= 1:
            errors.append("face_strength must be between 0 and 1")
        output_count = options.get("output_count")
        if not isinstance(output_count, int) or not 1 <= output_count <= 9:
            errors.append("output_count must be an integer between 1 and 9")

    negative_prompt = template.get("negative_prompt")
    if not isinstance(negative_prompt, list) or not negative_prompt:
        errors.append("negative_prompt must not be empty")

    return errors


def build_mock_task(template: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    prompt = build_prompt(template)
    negative_prompt = ", ".join(template.get("negative_prompt") or [])
    request_body = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "ratio": template.get("ratio"),
        "quality": (template.get("options") or {}).get("quality"),
        "face_strength": (template.get("options") or {}).get("face_strength"),
        "output_count": (template.get("options") or {}).get("output_count"),
    }
    return {
        "task_id": f"test_{template.get('template_id')}",
        "status": "failed" if errors else "completed",
        "template": {
            "template_id": template.get("template_id"),
            "category": template.get("category"),
            "title": template.get("title"),
            "ratio": template.get("ratio"),
            "style": template.get("style"),
        },
        "image_request": {
            "provider": "mock",
            "dry_run": True,
            "request_body": request_body,
        },
        "image_response": {
            "provider_task_id": f"mock_{template.get('template_id')}",
            "image_urls": [],
            "raw": {
                "mode": "mock",
                "message": "No real image API was called.",
            },
        },
        "errors": errors,
    }


def build_prompt(template: dict[str, Any]) -> str:
    blocks = template.get("prompt_blocks") or {}
    negative_prompt = ", ".join(template.get("negative_prompt") or [])
    return f"""【模板名称】
{template.get("title")}

【分类】
{template.get("category")}

【画幅】
{template.get("ratio")}

【风格】
{template.get("style")}

【生成目标】
{blocks.get("subject")}

【脸部保真】
{blocks.get("face")}

【服装造型】
{blocks.get("clothing")}

【场景环境】
{blocks.get("scene")}

【光影氛围】
{blocks.get("lighting")}

【镜头构图】
{blocks.get("camera")}

【画质要求】
{blocks.get("quality")}

【商业用途】
{blocks.get("commercial_use")}

【安全与品质要求】
保留用户真实五官、脸型、肤色，不要过度磨皮，不要低俗，不要裸露，不要生成夸张身体比例，服装完整得体，整体高级、干净、商业可用。

【负面提示】
{negative_prompt}""".strip()


def check_image_env(root: Path) -> dict[str, Any]:
    values = read_env_file(root / ".env")
    provider = values.get("AI_IMAGE_PROVIDER", "mock")
    dry_run = values.get("AI_IMAGE_DRY_RUN", "true").lower() in {"1", "true", "yes", "on"}
    api_url = values.get("AI_IMAGE_API_URL", "")
    api_key = values.get("AI_IMAGE_API_KEY", "")
    errors = []
    warnings = []

    if provider not in {"mock", "http"}:
        errors.append("AI_IMAGE_PROVIDER must be mock or http")
    if not dry_run and provider == "http" and not api_url:
        errors.append("AI_IMAGE_API_URL is required when AI_IMAGE_PROVIDER=http and AI_IMAGE_DRY_RUN=false")
    if not dry_run and provider == "http" and not api_key:
        warnings.append("AI_IMAGE_API_KEY is empty. This is only OK if your provider does not require a key.")

    return {
        "env_file": str(root / ".env"),
        "env_file_exists": (root / ".env").exists(),
        "provider": provider,
        "dry_run": dry_run,
        "api_url_set": bool(api_url),
        "api_key_set": bool(api_key),
        "errors": errors,
        "warnings": warnings,
    }


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def generate_catalog(root: Path) -> dict[str, Any]:
    templates = list_templates(root)
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    catalog_path = docs_dir / "template_catalog.md"
    lines = [
        "# Template Catalog",
        "",
        "Generated by `kimi-photo-template-tools`.",
        "",
        "| Template ID | Category | Title | Ratio | Style | Quality | Face Strength |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for item in templates:
        lines.append(
            f"| {item['template_id']} | {item['category']} | {item['title']} | "
            f"{item['ratio']} | {item['style']} | {item['quality']} | {item['face_strength']} |"
        )
    lines.append("")
    catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"catalog_path": str(catalog_path), "templates": len(templates)}


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fail(message: str) -> None:
    emit({"error": message})
    raise SystemExit(1)


if __name__ == "__main__":
    main()
