#!/usr/bin/env python3
"""export_prompt_pack.py — 按主题导出 Prompt Pack。

从本地 data/prompts/ 目录读取 prompt 文档，
或从 metadata image-index.jsonl 中精选的图生成 Prompt 摘要包，
输出为一个结构化的 markdown 文件或 zip 包。

用法:
  python export_prompt_pack.py list                    # 列出所有主题
  python export_prompt_pack.py export bodycon_dress      # 导出单主题
  python export_prompt_pack.py export bodycon_dress --format markdown
  python export_prompt_pack.py export bodycon_dress --format zip
  python export_prompt_pack.py export all --output ./prompt-packs
"""

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path


def find_prompt_files(prompts_dir: Path, theme: str = "") -> list[Path]:
    """扫描 prompt 目录下的所有 .md 文件，可选按主题过滤"""
    if not prompts_dir.exists():
        return []

    all_files = sorted(prompts_dir.rglob("*.md"))
    if not theme or theme == "all":
        return all_files

    # 按主题名匹配目录或文件名
    theme_slug = theme.lower().replace("_", "-")
    return [
        p for p in all_files
        if theme_slug in p.stem.lower() or theme_slug in str(p.relative_to(prompts_dir)).lower()
    ]


def build_markdown_pack(theme: str, prompt_files: list[Path],
                        selected_images: list[dict]) -> str:
    """生成主题 Prompt Pack 的 Markdown 内容"""
    lines = []
    lines.append(f"# Prompt Pack: {theme}")
    lines.append(f"")
    lines.append(f"> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> Prompt 数: {len(prompt_files)}")
    lines.append(f"> 精选参考图: {len(selected_images)}")
    lines.append(f"")
    lines.append("---")
    lines.append("")

    # 参考图部分
    if selected_images:
        lines.append("## [camera]  参考图")
        lines.append("")
        for img in selected_images[:20]:
            asset_id = img.get("asset_id", "?")
            image_file = img.get("image_file", "")
            notes = img.get("notes", "")
            tags = ", ".join(img.get("tags", []) or img.get("category", []))
            lines.append(f"- **{asset_id}**")
            if image_file:
                lines.append(f"  - 路径: `{image_file}`")
            if tags:
                lines.append(f"  - 标签: {tags}")
            if notes:
                lines.append(f"  - 备注: {notes}")
            lines.append("")
        if len(selected_images) > 20:
            lines.append(f"... 以及 {len(selected_images) - 20} 张更多参考图")
            lines.append("")

    # Prompt 文件内容
    lines.append("## [meta]  Prompt 文件")
    lines.append("")
    for pf in prompt_files:
        rel = pf.relative_to(pf.parents[2] if len(pf.parents) > 2 else pf.parent)
        lines.append(f"### {pf.stem}")
        lines.append(f"")
        lines.append(f"路径: `{rel}`")
        lines.append(f"")
        content = pf.read_text(encoding="utf-8").strip()
        if content:
            lines.append("```text")
            lines.append(content)
            lines.append("```")
        else:
            lines.append("_(空文件)_")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def load_index_entries(index_path: str, theme: str = "") -> list[dict]:
    """从 image-index.jsonl 中按主题筛选条目"""
    if not os.path.exists(index_path):
        return []
    entries = []
    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not theme or theme == "all":
                    entries.append(entry)
                else:
                    cats = entry.get("category", []) or entry.get("tags", [])
                    series = entry.get("series", "")
                    if any(theme.replace("_", " ") in str(c).lower() for c in cats):
                        entries.append(entry)
                    elif theme.lower().replace("_", "-") in series.lower():
                        entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def main():
    parser = argparse.ArgumentParser(description="Prompt Pack 导出工具")
    sub = subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出可用主题")

    export_parser = sub.add_parser("export", help="导出 Prompt Pack")
    export_parser.add_argument("theme", help="主题名称，或 'all'")
    export_parser.add_argument("--format", choices=["markdown", "zip"],
                               default="markdown", help="输出格式")
    export_parser.add_argument("--output", default="./prompt-packs",
                               help="输出目录")

    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    prompts_dir = project_dir / "data" / "prompts"
    index_path = project_dir / "data" / "metadata" / "image-index.jsonl"

    themes = [
        "bodycon_dress", "mini_dress", "sheer_panel_dress",
        "dudou_modern", "floral_skater_dress", "swimwear_editorial",
        "siuf_2026", "hotel_editorial",
    ]

    if args.command == "list":
        print("可用主题:")
        for t in themes:
            files = find_prompt_files(prompts_dir, t)
            images = load_index_entries(str(index_path), t)
            print(f"  📁 {t}  (prompt: {len(files)}, 参考图: {len(images)})")
        # 也列出 prompts 目录中存在的子目录
        if prompts_dir.exists():
            for d in sorted(prompts_dir.iterdir()):
                if d.is_dir() and d.name not in themes:
                    md_count = len(list(d.rglob("*.md")))
                    print(f"  📁 {d.name}  (prompt: {md_count})")
        return

    if args.command == "export":
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        themes_to_export = themes if args.theme == "all" else [args.theme]

        for theme in themes_to_export:
            prompt_files = find_prompt_files(prompts_dir, theme)
            selected_images = load_index_entries(str(index_path), theme)

            if not prompt_files and not selected_images:
                print(f"[warn]   主题 '{theme}' 没有 prompt 或参考图")
                continue

            content = build_markdown_pack(theme, prompt_files, selected_images)

            if args.format == "markdown":
                out_file = output_dir / f"prompt-pack-{theme}.md"
                out_file.write_text(content, encoding="utf-8")
                print(f"[ok]  导出: {out_file} ({len(content)} 字符)")

            elif args.format == "zip":
                zip_path = output_dir / f"prompt-pack-{theme}.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    # 添加 markdown 包
                    md_name = f"prompt-pack-{theme}.md"
                    zf.writestr(md_name, content)
                    # 添加 prompt 文件
                    for pf in prompt_files:
                        arcname = f"prompts/{pf.relative_to(prompts_dir)}"
                        zf.write(str(pf), arcname)
                print(f"[ok]  导出: {zip_path} ({zip_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
