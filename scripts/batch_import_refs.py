#!/usr/bin/env python3
"""batch_import_refs.py — 批量导入本地参考图到 COS。

扫描 local_cache/inbox/ 目录下的所有图片，
自动计算 hash、检测重复、提示用户填写 metadata，
然后上传到 COS 并写入 image-index.jsonl。

用法:
  python batch_import_refs.py
  python batch_import_refs.py --inbox /path/to/inbox
  python batch_import_refs.py --source-domain pinterest.com --license-status reference_only
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

COS_SECRET_ID = os.getenv("COS_SECRET_ID")
COS_SECRET_KEY = os.getenv("COS_SECRET_KEY")
COS_REGION = os.getenv("COS_REGION", "ap-shanghai")
COS_BUCKET_REF = os.getenv("COS_BUCKET_REF")
COS_BUCKET_GEN = os.getenv("COS_BUCKET_GEN")
COS_BUCKET_DOC = os.getenv("COS_BUCKET_DOC")

if not COS_SECRET_ID or not COS_SECRET_KEY:
    print("错误: 请在 .env 中配置 COS_SECRET_ID 和 COS_SECRET_KEY", file=sys.stderr)
    sys.exit(1)

COS_AVAILABLE = False
try:
    from qcloud_cos import CosConfig, CosS3Client
    COS_AVAILABLE = True
except ImportError:
    pass

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}


def is_image(file: Path) -> bool:
    return file.suffix.lower() in IMAGE_EXTENSIONS and not file.name.startswith(".")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_existing_hashes(index_path: str) -> set:
    hashes = set()
    if not os.path.exists(index_path):
        return hashes
    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                h = entry.get("sha256", "")
                if h:
                    hashes.add(h)
            except json.JSONDecodeError:
                continue
    return hashes


def prompt_metadata(filename: str, default_series: str) -> dict:
    """交互式提示用户填写 metadata。可替换为 GUI 或预设值。"""
    print(f"\n─── {filename} ───")
    series = input(f"  系列 (默认: {default_series}): ").strip() or default_series
    category_raw = input(f"  分类标签 (逗号分隔): ").strip()
    category = [c.strip() for c in category_raw.split(",") if c.strip()] if category_raw else []
    source_url = input("  来源 URL: ").strip()
    source_domain = input("  来源域名: ").strip()
    notes = input("  备注: ").strip()
    rating_raw = input("  评分 1-5 (默认 3): ").strip()
    rating = int(rating_raw) if rating_raw.isdigit() else 3
    return {
        "series": series,
        "category": category,
        "source_url": source_url,
        "source_domain": source_domain,
        "notes": notes,
        "rating": rating,
    }


def main():
    parser = argparse.ArgumentParser(description="批量导入参考图")
    parser.add_argument("--inbox", default=None,
                        help="inbox 目录路径（默认: local_cache/inbox）")
    parser.add_argument("--series", default="uncategorized",
                        help="默认系列名称")
    parser.add_argument("--source-domain", default="",
                        help="默认来源域名")
    parser.add_argument("--license-status", default="unknown_reference_only",
                        help="默认授权状态")
    parser.add_argument("--non-interactive", action="store_true",
                        help="非交互模式，使用默认值")
    parser.add_argument("--dry-run", action="store_true",
                        help="只扫描不上传")
    args = parser.parse_args()

    # 定位 inbox 目录
    script_dir = Path(__file__).parent.resolve()
    if args.inbox:
        inbox_dir = Path(args.inbox)
    else:
        inbox_dir = script_dir.parent / "local_cache" / "inbox"

    if not inbox_dir.exists():
        print(f"错误: inbox 目录不存在: {inbox_dir}", file=sys.stderr)
        sys.exit(1)

    index_path = script_dir.parent / "data" / "metadata" / "image-index.jsonl"
    existing_hashes = load_existing_hashes(str(index_path))

    # 扫描图片
    images = sorted([p for p in inbox_dir.iterdir() if is_image(p)])
    if not images:
        print(f"📭 inbox 为空: {inbox_dir}")
        return

    print(f"[camera]  发现 {len(images)} 张图片\n")

    if not COS_AVAILABLE and not args.dry_run:
        print("[warn]   未安装 cos-python-sdk-v5，请先安装: pip install cos-python-sdk-v5")
        sys.exit(1)

    if not args.dry_run and COS_AVAILABLE:
        config = CosConfig(
            Region=COS_REGION,
            SecretId=COS_SECRET_ID,
            SecretKey=COS_SECRET_KEY,
        )
        client = CosS3Client(config)

    uploaded = 0
    skipped = 0
    dt_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for img in images:
        print(f"[hash]  计算 hash: {img.name}")
        file_hash = sha256_file(str(img))

        if file_hash in existing_hashes:
            print(f"⏭  跳过（重复）: {img.name}")
            skipped += 1
            continue

        if args.non_interactive:
            meta = {
                "series": args.series,
                "category": [],
                "source_url": "",
                "source_domain": args.source_domain,
                "notes": "",
                "rating": 3,
            }
        else:
            meta = prompt_metadata(img.name, args.series)

        # 构建 metadata 条目
        series_slug = meta["series"].lower().replace(" ", "-")
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_compact = datetime.now().strftime("%Y%m%d")
        hash_short = file_hash[:6]
        asset_id = f"ref_{date_compact}_{hash_short}"
        cos_key = f"ref/{series_slug}/{date_str}/source/{date_compact}_{series_slug}_{img.name}"

        entry = {
            "asset_id": asset_id,
            "type": "reference",
            "project": "AI Fashion Director",
            "series": meta["series"],
            "category": meta["category"],
            "source_url": meta["source_url"],
            "source_domain": meta["source_domain"] or args.source_domain,
            "collected_at": dt_now,
            "license_status": args.license_status,
            "usage_scope": "private_research_reference",
            "do_not_publish": True,
            "image_file": f"cos://{COS_BUCKET_REF}/{cos_key}" if not args.dry_run else "",
            "tags": meta["category"],
            "quality_score": meta["rating"],
            "notes": meta["notes"],
            "created_at": dt_now,
            "sha256": file_hash,
        }

        if not args.dry_run:
            print(f"[up]   上传: {COS_BUCKET_REF}/{cos_key} ...")
            with open(str(img), "rb") as fp:
                client.put_object(
                    Bucket=COS_BUCKET_REF,
                    Body=fp,
                    Key=cos_key,
                )
            print(f"[ok]  上传完成")

        # 写入索引
        with open(str(index_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"[meta]  已记录: {asset_id} ({img.name})")
        existing_hashes.add(file_hash)
        uploaded += 1

        # 移动文件到 processed
        if not args.dry_run:
            processed_dir = script_dir.parent / "local_cache" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            img.rename(processed_dir / img.name)

    print(f"\n{'='*40}")
    print(f"[ok]  上传: {uploaded}")
    print(f"⏭  跳过重复: {skipped}")
    print(f"📁 剩余: {len(images) - uploaded - skipped}")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()
