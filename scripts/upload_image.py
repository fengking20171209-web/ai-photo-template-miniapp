#!/usr/bin/env python3
"""upload_image.py — 上传单张图片到腾讯云 COS，生成 metadata 并写入本地索引。

用法:
  python upload_image.py /path/to/image.png \\
      --type generated \\
      --series "CC Bodycon v2" \\
      --look "black_spaghetti_bodycon_hotel" \\
      --category bodycon_dress mini_dress \\
      --notes "Good body line"

必填参数:
  path                   图片文件路径
  --type                 类型: generated | reference

可选参数:
  --series              系列名称，如 "CC Bodycon v2"
  --look                 Look 名称
  --category            分类标签，可多个
  --outfit-silhouette   服装廓形
  --outfit-fabric       面料
  --outfit-color        颜色
  --pose                姿态
  --scene               场景
  --camera              镜头描述
  --source-url          来源 URL（外部参考图必填）
  --source-domain       来源域名
  --search-query        搜索关键词
  --license-status      授权状态
  --usage-scope         使用范围
  --rating              评分 1-5
  --notes               备注
  --no-thumb            不上传缩略图
  --dry-run             只生成 metadata，不上传
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from dotenv import load_dotenv

# ── 加载 .env ──────────────────────────────────────────────────────────
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

# ── 延迟导入 COS SDK（仅在完整模式下需要）────────────────────────────
COS_AVAILABLE = False
try:
    from qcloud_cos import CosConfig, CosS3Client
    COS_AVAILABLE = True
except ImportError:
    pass


def get_client():
    config = CosConfig(
        Region=COS_REGION,
        SecretId=COS_SECRET_ID,
        SecretKey=COS_SECRET_KEY,
    )
    return CosS3Client(config)


# ── 工具函数 ────────────────────────────────────────────────────────────

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_asset_id(prefix: str, date_str: str, hash_prefix: str) -> str:
    return f"{prefix}_{date_str}_{hash_prefix}"


def compute_cos_key(file_type: str, series: str, date_str: str,
                    subdir: str, filename: str) -> str:
    base = "gen" if file_type == "generated" else "ref"
    series_slug = series.lower().replace(" ", "-").replace("_", "-")
    return f"{base}/{series_slug}/{date_str}/{subdir}/{filename}"


def upload_file(client, bucket: str, local_path: str, cos_key: str) -> str:
    """上传文件并返回 COS URL"""
    if not COS_AVAILABLE:
        raise RuntimeError("cos-python-sdk-v5 未安装，无法上传")
    with open(local_path, "rb") as fp:
        response = client.put_object(
            Bucket=bucket,
            Body=fp,
            Key=cos_key,
        )
    # 构建标准 COS URL
    return f"cos://{bucket}/{cos_key}"


def save_metadata(index_path: str, entry: dict):
    """追加一条 metadata 到本地 JSONL 索引"""
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── 主流程 ──────────────────────────────────────────────────────────────

def build_metadata(args, file_hash: str, date_str: str,
                   cos_url: str | None) -> dict:
    dt_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    hash_short = file_hash[:6]
    asset_id = generate_asset_id(
        "img" if args.type == "generated" else "ref",
        date_str.replace("-", ""),
        hash_short,
    )

    entry = {
        "asset_id": asset_id,
        "type": args.type,
        "project": "AI Fashion Director",
        "series": args.series or "",
        "look": args.look or "",
        "category": args.category or [],
        "source_url": args.source_url,
        "source_domain": args.source_domain,
        "search_query": args.search_query,
        "collected_at": dt_now,
        "license_status": args.license_status or (
            "self_generated" if args.type == "generated"
            else "unknown_reference_only"
        ),
        "usage_scope": args.usage_scope or "private_research_reference",
        "do_not_publish": args.type == "reference",
        "image_file": cos_url or "",
        "tags": args.category or [],
        "quality_score": args.rating or 0,
        "notes": args.notes or "",
        "created_at": dt_now,
        "sha256": file_hash,
    }

    # 服装结构化数据（仅 generated 类型）
    if args.type == "generated":
        outfit = {}
        if args.outfit_silhouette:
            outfit["silhouette"] = args.outfit_silhouette
        if args.outfit_fabric:
            outfit["fabric"] = args.outfit_fabric
        if args.outfit_color:
            outfit["color"] = args.outfit_color
        if outfit:
            entry["outfit"] = outfit
        if args.pose:
            entry["pose"] = [args.pose] if isinstance(args.pose, str) else args.pose
        if args.scene:
            entry["scene"] = args.scene
        if args.camera:
            entry["camera"] = args.camera

    return entry


def main():
    parser = argparse.ArgumentParser(description="上传图片到 COS 并记录 metadata")
    parser.add_argument("path", help="图片文件路径")
    parser.add_argument("--type", required=True,
                        choices=["generated", "reference"],
                        help="图片类型")
    parser.add_argument("--series", help="系列名称")
    parser.add_argument("--look", help="Look 名称")
    parser.add_argument("--category", nargs="*", default=[],
                        help="分类标签")
    parser.add_argument("--outfit-silhouette", help="服装廓形")
    parser.add_argument("--outfit-fabric", help="面料")
    parser.add_argument("--outfit-color", help="颜色")
    parser.add_argument("--pose", help="姿态")
    parser.add_argument("--scene", help="场景")
    parser.add_argument("--camera", help="镜头描述")
    parser.add_argument("--source-url", help="来源 URL")
    parser.add_argument("--source-domain", help="来源域名")
    parser.add_argument("--search-query", help="搜索关键词")
    parser.add_argument("--license-status", help="授权状态")
    parser.add_argument("--usage-scope", help="使用范围")
    parser.add_argument("--rating", type=int, default=0,
                        help="评分 1-5")
    parser.add_argument("--notes", help="备注")
    parser.add_argument("--no-thumb", action="store_true",
                        help="不上传缩略图")
    parser.add_argument("--dry-run", action="store_true",
                        help="只生成 metadata，不上传")
    args = parser.parse_args()

    local_path = Path(args.path)
    if not local_path.exists():
        print(f"错误: 文件不存在: {local_path}", file=sys.stderr)
        sys.exit(1)

    # 计算 hash
    print(f"[hash]  计算 SHA256...")
    file_hash = sha256_file(str(local_path))
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_compact = datetime.now().strftime("%Y%m%d")

    # 目标 bucket
    bucket = COS_BUCKET_GEN if args.type == "generated" else COS_BUCKET_REF
    series_slug = (args.series or "uncategorized").lower().replace(" ", "-")

    # 上传原图
    cos_url = None
    if not args.dry_run:
        if not COS_AVAILABLE:
            print("⚠  未安装 cos-python-sdk-v5，尝试安装: pip install cos-python-sdk-v5",
                  file=sys.stderr)
            sys.exit(1)
        client = get_client()
        cos_key = compute_cos_key(args.type, series_slug, date_str,
                                  "original", local_path.name)
        print(f"[upload]  上传到 COS: {bucket}/{cos_key} ...")
        cos_url = upload_file(client, bucket, str(local_path), cos_key)
        print(f"[ok] 上传完成: {cos_url}")
    else:
        print("[finish]  DRY RUN: 跳过上传")

    # 构建 metadata
    entry = build_metadata(args, file_hash, date_compact, cos_url)
    print(f"[meta]  生成 metadata (asset_id: {entry['asset_id']})")

    # 写入本地索引
    index_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "data", "metadata", "image-index.jsonl",
    )
    save_metadata(index_path, entry)
    print(f"[saved]  已写入索引: {index_path}")

    # 输出 JSON
    print("\n" + json.dumps(entry, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
