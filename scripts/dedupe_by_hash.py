#!/usr/bin/env python3
"""dedupe_by_hash.py — 基于 SHA256 对 COS 图片去重。

扫描指定目录（本地或 COS），计算/读取 hash，
标记重复文件并列出重复项，可选删除。

用法:
  python dedupe_by_hash.py check         # 检查本地索引中的重复
  python dedupe_by_hash.py check --dir ./inbox  # 检查目录
  python dedupe_by_hash.py merge         # 合并重复项（保留第一条，其余标注）
  python dedupe_by_hash.py cleanup       # 列出重复项供手动处理
"""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_directory(directory: Path) -> dict[str, list[Path]]:
    """扫描目录，按 hash 分组返回 {hash: [paths]}"""
    hash_map = defaultdict(list)
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

    files = [p for p in directory.rglob("*") if p.suffix.lower() in extensions]
    for i, f in enumerate(files):
        print(f"\r[hash]  扫描 [{i+1}/{len(files)}]: {f.name}", end="")
        h = sha256_file(str(f))
        hash_map[h].append(f)
    print()

    return dict(hash_map)


def scan_index(index_path: str) -> dict[str, list[dict]]:
    """扫描本地 image-index.jsonl，按 sha256 分组"""
    hash_map = defaultdict(list)
    if not os.path.exists(index_path):
        return {}
    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                h = entry.get("sha256", "")
                if h:
                    hash_map[h].append(entry)
            except json.JSONDecodeError:
                continue
    return dict(hash_map)


def report_duplicates(hash_map: dict, source_name: str = ""):
    """输出重复报告"""
    dup_count = 0
    total_size_saved = 0

    print(f"\n{'='*60}")
    print(f"重复检查报告{(' — ' + source_name) if source_name else ''}")
    print(f"{'='*60}")

    for h, items in sorted(hash_map.items()):
        if len(items) <= 1:
            continue
        dup_count += 1
        print(f"\n🔁 重复 (hash: {h[:12]}...) x{len(items)}:")
        for item in items:
            path = item.get("image_file", "") if isinstance(item, dict) else str(item)
            name = item.get("asset_id", item.name) if isinstance(item, dict) else item.name
            size = item.stat().st_size if isinstance(item, Path) else 0
            total_size_saved += size * (len(items) - 1)
            print(f"  - {name}  ({size // 1024} KB)")

    print(f"\n🔢 重复组数: {dup_count}")
    if total_size_saved > 0:
        print(f"[saved]  可节省空间: ~{total_size_saved // (1024*1024)} MB")

    return dup_count


def main():
    parser = argparse.ArgumentParser(description="图片去重工具")
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="检查重复")
    check_parser.add_argument("--dir", help="扫描目录（默认扫描索引）")
    check_parser.add_argument("--index", default=None,
                              help="索引文件路径")

    sub.add_parser("merge", help="合并重复（索引中标记为 duplicated）")
    sub.add_parser("cleanup", help="列出重复供手动清理")

    args = parser.parse_args()

    # 定位索引路径
    script_dir = Path(__file__).parent.resolve()
    index_path = args.index or str(script_dir.parent / "data" / "metadata" / "image-index.jsonl")

    if args.command == "check":
        if args.dir:
            target_dir = Path(args.dir)
            if not target_dir.exists():
                print(f"错误: 目录不存在: {target_dir}", file=sys.stderr)
                sys.exit(1)
            hash_map = scan_directory(target_dir)
            report_duplicates(hash_map, str(target_dir))
        else:
            hash_map = scan_index(index_path)
            report_duplicates(hash_map, "image-index.jsonl")

    elif args.command == "merge":
        hash_map = scan_index(index_path)
        if not hash_map:
            print("索引为空或不存在")
            return

        # 读取完整索引，标记重复
        lines = []
        seen_hashes = set()
        merged_count = 0

        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                h = entry.get("sha256", "")
                if h in seen_hashes:
                    entry["dup_of"] = "see_previous"
                    merged_count += 1
                else:
                    seen_hashes.add(h)
                lines.append(json.dumps(entry, ensure_ascii=False))

        # 写回
        with open(index_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        print(f"[ok]  合并完成，标记 {merged_count} 条重复")

    elif args.command == "cleanup":
        hash_map = scan_index(index_path)
        count = report_duplicates(hash_map, "image-index.jsonl")
        if count == 0:
            print("\n[done]  没有发现重复！")
        else:
            print(f"\n[idea]  如需删除 COS 上的重复文件，请审查后再操作")


if __name__ == "__main__":
    main()
