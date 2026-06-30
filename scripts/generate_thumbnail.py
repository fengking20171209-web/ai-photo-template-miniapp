#!/usr/bin/env python3
"""generate_thumbnail.py — 生成缩略图：preview (1600px webp)、thumb (512px webp)、tiny (128px jpg)。

用法:
  python generate_thumbnail.py /path/to/image.png
  python generate_thumbnail.py --input-dir ./raw --output-dir ./thumbs
  python generate_thumbnail.py --upload  # 生成后上传到 COS
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

COS_AVAILABLE = False
try:
    from qcloud_cos import CosConfig, CosS3Client
    COS_AVAILABLE = True
except ImportError:
    pass

THUMB_AVAILABLE = False
try:
    from PIL import Image
    THUMB_AVAILABLE = True
except ImportError:
    pass

PREVIEW_WIDTH = int(os.getenv("THUMBNAIL_PREVIEW_WIDTH", "1600"))
THUMB_WIDTH = int(os.getenv("THUMBNAIL_THUMB_WIDTH", "512"))
TINY_WIDTH = int(os.getenv("THUMBNAIL_TINY_WIDTH", "128"))
QUALITY = int(os.getenv("THUMBNAIL_QUALITY", "85"))


def generate_thumbnails(input_path: Path, output_dir: Path) -> dict[str, Path]:
    """生成三档缩略图，返回 {variant: path}"""
    if not THUMB_AVAILABLE:
        raise RuntimeError("Pillow 未安装: pip install Pillow")

    img = Image.open(input_path)
    img = img.convert("RGB")  # 统一 RGB，消除 alpha 通道问题

    w, h = img.size
    results = {}

    variants = [
        ("preview", PREVIEW_WIDTH, "webp"),
        ("thumb", THUMB_WIDTH, "webp"),
        ("tiny", TINY_WIDTH, "jpg"),
    ]

    stem = input_path.stem
    for variant, target_width, fmt in variants:
        if w > target_width:
            ratio = target_width / w
            new_h = int(h * ratio)
            resized = img.resize((target_width, new_h), Image.LANCZOS)
        else:
            resized = img

        out_name = f"{stem}__{variant}.{fmt}"
        out_path = output_dir / variant / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        save_kwargs = {"format": {"webp": "WEBP", "jpg": "JPEG", "png": "PNG"}.get(fmt, fmt.upper()), "quality": QUALITY}
        if fmt == "jpg":
            save_kwargs["optimize"] = True

        resized.save(str(out_path), **save_kwargs)
        results[variant] = out_path
        print(f"  [ok]  {variant}: {out_path} ({out_path.stat().st_size // 1024} KB)")

    return results


def upload_thumbnails(client, bucket: str, cos_base_key: str,
                      results: dict[str, Path]) -> dict[str, str]:
    """上传缩略图到 COS，返回 {variant: cos_url}"""
    cos_urls = {}
    for variant, local_path in results.items():
        cos_key = f"{cos_base_key}/{variant}/{local_path.name}"
        with open(str(local_path), "rb") as fp:
            client.put_object(Bucket=bucket, Body=fp, Key=cos_key)
        cos_urls[variant] = f"cos://{bucket}/{cos_key}"
        print(f"  [up]   {variant}: {cos_key}")
    return cos_urls


def main():
    parser = argparse.ArgumentParser(description="图片缩略图生成器")
    parser.add_argument("path", nargs="?", help="单张图片路径")
    parser.add_argument("--input-dir", help="输入目录（批量处理）")
    parser.add_argument("--output-dir", default="./thumbs",
                        help="缩略图输出目录（默认 ./thumbs）")
    parser.add_argument("--upload", action="store_true",
                        help="生成后上传到 COS")
    parser.add_argument("--cos-key-prefix", default="",
                        help="COS 路径前缀，如 gen/cc-model/bodycon-v2/2026-05-28")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    # 收集图片
    images: list[Path] = []
    if args.path:
        images.append(Path(args.path))
    elif args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"错误: 输入目录不存在: {input_dir}", file=sys.stderr)
            sys.exit(1)
        images = sorted([
            p for p in input_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ])
    else:
        parser.print_help()
        sys.exit(1)

    if not images:
        print("没有找到图片")
        return

    if not THUMB_AVAILABLE:
        print("错误: 请安装 Pillow: pip install Pillow", file=sys.stderr)
        sys.exit(1)

    # COS 客户端（仅 upload 模式）
    client = None
    if args.upload:
        if not COS_AVAILABLE:
            print("错误: 请安装 cos-python-sdk-v5", file=sys.stderr)
            sys.exit(1)
        cos_secret_id = os.getenv("COS_SECRET_ID")
        cos_secret_key = os.getenv("COS_SECRET_KEY")
        cos_region = os.getenv("COS_REGION", "ap-shanghai")
        bucket = os.getenv("COS_BUCKET_GEN")
        if not all([cos_secret_id, cos_secret_key, bucket]):
            print("错误: 请在 .env 中配置 COS 凭证", file=sys.stderr)
            sys.exit(1)
        config = CosConfig(Region=cos_region,
                           SecretId=cos_secret_id,
                           SecretKey=cos_secret_key)
        client = CosS3Client(config)
    else:
        bucket = ""

    for img_path in images:
        print(f"\n📷 {img_path.name}")
        results = generate_thumbnails(img_path, output_dir)

        if args.upload and client:
            cos_key = (args.cos_key_prefix or
                       f"gen/{img_path.stem}/{img_path.parent.name}")
            upload_thumbnails(client, bucket, cos_key, results)

    print(f"\n[ok]  处理完成: {len(images)} 张图片")


if __name__ == "__main__":
    main()

