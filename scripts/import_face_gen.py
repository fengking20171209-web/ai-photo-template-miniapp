#!/usr/bin/env python3
"""import_face_gen.py — 生图智能导入：自动分类 + COS 上传 + 缩略图 + 索引记录

用法:
  # 扫描 face/ 目录所有新文件并导入
  python scripts/import_face_gen.py

  # 指定输入目录（例如从生图输出目录导入）
  python scripts/import_face_gen.py --input-dir D:/output/latest

  # 指定系列名（当无法从路径推断时使用）
  python scripts/import_face_gen.py --series "SIUF 2026"

  # 非交互模式 + 仅预览不上传
  python scripts/import_face_gen.py --dry-run --non-interactive

  # 静默模式（无交互，自动处理全部）
  python scripts/import_face_gen.py --non-interactive
"""

import argparse
import hashlib
import json
import os
import re
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ── 加载 .env ──────────────────────────────────────────────────────────
load_dotenv()

COS_SECRET_ID = os.getenv("COS_SECRET_ID")
COS_SECRET_KEY = os.getenv("COS_SECRET_KEY")
COS_REGION = os.getenv("COS_REGION", "ap-shanghai")
COS_BUCKET_GEN = os.getenv("COS_BUCKET_GEN")
COS_BUCKET_REF = os.getenv("COS_BUCKET_REF")

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

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# ── ================================================================ ──
#  分类引擎 — 基于文件名/路径关键词匹配 taxonomy + 系列模板
# ── ================================================================ ──

# 已知系列别名 → 规范化系列名
SERIES_ALIASES = {
    "siuf": "siuf-2026",
    "siuf2026": "siuf-2026",
    "siuf_2026": "siuf-2026",
    "dudou": "dudou-modern",
    "肚兜": "dudou-modern",
    "黑丝": "siuf-2026",
    "白纱": "siuf-2026",
    "face": "face-portrait",
    "portrait": "face-portrait",
    "头像": "face-portrait",
    "refer": "face-reference",
    "ref": "face-reference",
    "参考": "face-reference",
}

# 主题关键词 → taxonomy theme
THEME_KEYWORDS = {
    "bodycon": "bodycon_dress",
    "修 bodycon": "bodycon_dress",
    "mini": "mini_dress",
    "短裙": "mini_dress",
    "sheer": "sheer_panel_dress",
    "透视": "sheer_panel_dress",
    "dudou": "dudou_modern",
    "肚兜": "dudou_modern",
    "floral": "floral_skater_dress",
    "碎花": "floral_skater_dress",
    "swim": "swimwear_editorial",
    "泳装": "swimwear_editorial",
    "bikini": "swimwear_editorial",
    "siuf": "siuf_2026",
    "hotel": "hotel_editorial",
    "酒店": "hotel_editorial",
    "lace": "lingerie_lace",
    "蕾丝": "lingerie_lace",
    "silk": "luxury_silk",
    "satin": "luxury_satin",
    "旗袍": "oriental_cheongsam",
    "汉服": "oriental_hanfu",
    "古风": "oriental_hanfu",
    "sport": "sporty_active",
    "运动": "sporty_active",
    "制服": "uniform_office",
    "secretary": "uniform_office",
    "office": "uniform_office",
    "职业": "uniform_office",
    "cyber": "cyber_futuristic",
    "未来": "cyber_futuristic",
    "gothic": "gothic_dark",
    "哥特": "gothic_dark",
    "barbie": "pink_barbie",
    "粉": "pink_barbie",
    "y2k": "y2k_retro",
    "retro": "y2k_retro",
    "复古": "y2k_retro",
    "western": "western_cowboy",
    "cowboy": "western_cowboy",
    "牛仔": "western_cowboy",
    "oriental": "oriental_chinoiserie",
    "东方": "oriental_chinoiserie",
    "水墨": "oriental_chinoiserie",
    "loungewear": "loungewear_casual",
    "居家": "loungewear_casual",
    "luxury": "luxury_gala",
    "gala": "luxury_gala",
    "晚宴": "luxury_gala",
    "tropical": "tropical_resort",
    "度假": "tropical_resort",
    "resort": "tropical_resort",
    "泳池": "tropical_resort",
    "minimalist": "minimalist_modern",
    "极简": "minimalist_modern",
    "chic": "metro_chic",
    "街拍": "metro_chic",
    "crystal": "crystal_luxury",
    "珠宝": "crystal_luxury",
    "outdoor": "outdoor_sport",
    "户外": "outdoor_sport",
    "pool": "pool_goddess",
    "french": "french_silk",
    "法式": "french_silk",
    "bridal": "white_lace_bridal",
    "婚纱": "white_lace_bridal",
    "新娘": "white_lace_bridal",
    "angel": "cyber_angel",
    "天使": "cyber_angel",
    "黑丝": "black_lace",
    "finale": "black_lace_finale",
}

# 面料关键词 → taxonomy fabric
FABRIC_KEYWORDS = {
    "lace": "lace_trim",
    "蕾丝": "lace_trim",
    "satin": "satin",
    "缎面": "satin",
    "silk": "silk",
    "真丝": "silk",
    "crepe": "stretch_crepe",
    "重磅": "ponte_double_knit",
    "jersey": "matte_compact_jersey",
    "棉": "matte_compact_jersey",
    "针织": "ribbed_knit",
    "mesh": "soft_mesh_overlay",
    "网纱": "soft_mesh_overlay",
    "牛仔": "denim",
    "皮革": "leather",
    "leather": "leather",
    "毛": "fur_fleece",
    "皮草": "fur_fleece",
    "丝绒": "velvet",
    "velvet": "velvet",
    "雪纺": "chiffon",
    "chiffon": "chiffon",
    "羊毛": "wool_cashmere",
    "亮片": "sequin_glitter",
    "sequin": "sequin_glitter",
}

# 场景关键词 → taxonomy scene
SCENE_KEYWORDS = {
    "hotel": "luxury_hotel_corridor",
    "酒店": "luxury_hotel_corridor",
    "走廊": "luxury_hotel_corridor",
    "corridor": "luxury_hotel_corridor",
    "city": "night_city_suite",
    "夜景": "night_city_suite",
    "城市": "night_city_suite",
    "bar": "lounge_bar",
    "酒吧": "lounge_bar",
    "lounge": "lounge_bar",
    "marble": "marble_lobby",
    "大理石": "marble_lobby",
    "lobby": "marble_lobby",
    "studio": "minimalist_studio",
    "棚拍": "minimalist_studio",
    "纯色背景": "minimalist_studio",
    "lake": "lakeside",
    "湖边": "lakeside",
    "水边": "lakeside",
    "cafe": "cafe_terrace",
    "咖啡": "cafe_terrace",
    "户外": "cafe_terrace",
    "pool": "poolside",
    "泳池": "poolside",
    "garden": "garden_park",
    "花园": "garden_park",
    "森林": "forest_nature",
    "forest": "forest_nature",
    "海滩": "beach_seaside",
    "beach": "beach_seaside",
    "海边": "beach_seaside",
    "古风": "oriental_palace",
    "宫殿": "oriental_palace",
    "宫廷": "oriental_palace",
    "studio": "photography_studio",
    "影棚": "photography_studio",
    "居家": "cozy_living_room",
    "卧室": "cozy_bedroom",
    "浴室": "bathroom_spa",
    "天台": "rooftop_terrace",
    "rooftop": "rooftop_terrace",
    "霓虹": "neon_city_night",
    "neon": "neon_city_night",
}

# 廓形/款式关键词 → taxonomy silhouette
SILHOUETTE_KEYWORDS = {
    "bodycon": "spaghetti_strap_bodycon",
    "包臀": "spaghetti_strap_bodycon",
    "紧身": "ruched_bodycon",
    "ruched": "ruched_bodycon",
    "bandage": "bandage_bodycon",
    "pencil": "pencil_midi_dress",
    "包裙": "pencil_midi_dress",
    "fit": "fit_and_flare",
    "a字": "fit_and_flare",
    "skater": "skater_dress",
    "伞裙": "skater_dress",
    "dudou": "dudou_halter",
    "肚兜": "dudou_halter",
    "挂脖": "dudou_halter",
    "halter": "dudou_halter",
    "中式": "oriental_bodycon",
    "旗袍": "oriental_bodycon",
    "抹胸": "strapless_corset",
    "corset": "strapless_corset",
    "吊带": "spaghetti_strap",
    "spaghetti": "spaghetti_strap",
    "镂空": "cutout_peekaboo",
    "cutout": "cutout_peekaboo",
    "开衩": "high_slit",
    "slit": "high_slit",
    "百褶": "pleated_skirt",
    "pleated": "pleated_skirt",
    "鱼尾": "mermaid_hem",
    "mermaid": "mermaid_hem",
    "连体": "bodysuit_one_piece",
    "bodysuit": "bodysuit_one_piece",
    "分体": "two_piece_separates",
    "two piece": "two_piece_separates",
}

# ── 工具函数 ────────────────────────────────────────────────────────────

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def generate_asset_id(prefix: str, date_compact: str, hash_prefix: str) -> str:
    return f"{prefix}_{date_compact}_{hash_prefix}"

def is_image(file: Path) -> bool:
    return file.suffix.lower() in IMAGE_EXTENSIONS and not file.name.startswith(".")

def load_existing_hashes(index_path: str) -> set:
    """从本地索引加载已有 hash 用于去重"""
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

def get_cos_client():
    """获取 COS 客户端"""
    if not COS_AVAILABLE:
        raise RuntimeError("cos-python-sdk-v5 未安装，请先: pip install cos-python-sdk-v5")
    if not all([COS_SECRET_ID, COS_SECRET_KEY, COS_BUCKET_GEN]):
        raise RuntimeError("请在 .env 中配置 COS_SECRET_ID、COS_SECRET_KEY、COS_BUCKET_GEN")
    config = CosConfig(
        Region=COS_REGION,
        SecretId=COS_SECRET_ID,
        SecretKey=COS_SECRET_KEY,
    )
    return CosS3Client(config)

# ── ================================================================ ──
#  智能分类引擎
# ── ================================================================ ──

class ImageClassifier:
    """根据文件路径、子目录、文件名推断分类信息"""

    # 颜色映射
    COLOR_MAP = {
        "black": "black", "dark": "black", " noir": "black",
        "white": "white", "ivory": "off_white", "cream": "off_white",
        "red": "red", "crimson": "red", "scarlet": "red",
        "emerald": "green", "green": "green", "sage": "green",
        "blue": "blue", "navy": "navy", "azure": "blue",
        "pink": "pink", "rose": "pink", "芭比": "pink",
        "gold": "gold", "golden": "gold", "crystal": "crystal",
        "purple": "purple", "violet": "purple", "lavender": "purple",
        "silver": "silver", "grey": "gray", "gray": "gray",
        "brown": "brown", "tan": "brown", "beige": "beige",
        "orange": "orange", "coral": "coral", "peach": "coral",
        "yellow": "yellow", "jade": "jade",
        "clear": "transparent", "sheer": "transparent",
    }

    def classify(self, filepath: Path, project_dir: Path) -> dict:
        """
        对单张图片进行智能分类。

        返回:
        {
            "series": str,           # 系列名（suggests from path/filename）
            "series_slug": str,      # 系列 slug
            "look": str,             # Look 名称
            "look_id": str,          # 编号（如有）
            "themes": [str],         # taxonomy theme 列表
            "silhouette": [str],     # 廓形列表
            "fabric": [str],         # 面料列表
            "color": [str],          # 颜色列表
            "scene": [str],          # 场景列表
            "pose": [str],           # 姿态（如果有线索）
            "category": [str],       # 综合分类标签
            "notes": str,            # 备注
            "rating": int,           # 默认评分（后续可手动改）
        }
        """
        # 从路径推断
        rel_path = filepath.resolve()
        stem = filepath.stem.lower()
        parent_dir = filepath.parent.name.lower()

        # 尝试判断系列 ← 优先子目录名
        series = self._detect_series(parent_dir, stem)
        series_slug = series.lower().replace(" ", "-").replace("_", "-")

        # 尝试提取 Look 编号和名称
        look_id, look_name = self._detect_look_id(stem)

        # 关键词分类
        themes = self._match_keywords(stem, THEME_KEYWORDS)
        silhouettes = self._match_keywords(stem, SILHOUETTE_KEYWORDS)
        fabrics = self._match_keywords(stem, FABRIC_KEYWORDS)
        scenes = self._match_keywords(stem, SCENE_KEYWORDS)
        colors = self._detect_colors(stem)

        # 组合分类标签
        category = list(set(themes + silhouettes + fabrics + scenes))

        # 生成备注
        notes_parts = []
        if look_name:
            notes_parts.append(f"Look: {look_name}")
        if colors:
            notes_parts.append(f"配色: {', '.join(colors)}")
        notes = " | ".join(notes_parts) if notes_parts else f"自动导入: {filepath.name}"

        return {
            "series": series,
            "series_slug": series_slug,
            "look": look_name or stem,
            "look_id": look_id or "",
            "themes": themes,
            "silhouette": silhouettes,
            "fabric": fabrics,
            "color": colors,
            "scene": scenes,
            "category": category,
            "notes": notes,
            "rating": 3,
        }

    def _detect_series(self, parent_dir: str, stem: str) -> str:
        """从父目录名或文件名推断系列"""
        # 先检查目录别名
        if parent_dir in SERIES_ALIASES:
            return SERIES_ALIASES[parent_dir]
        # 检查子目录名是否匹配已知系列
        for alias, series in SERIES_ALIASES.items():
            if alias in parent_dir:
                return series
        # 文件名包含系列关键词
        for alias, series in SERIES_ALIASES.items():
            if alias in stem:
                return series
        return "uncategorized"

    def _detect_look_id(self, stem: str) -> tuple:
        """从文件名提取编号和 Look 名"""
        # 模式: d01-crimson-satin 或 d01_crimson_satin
        m = re.match(r"(d?\d+)[-_]*(.+)", stem)
        if m:
            return m.group(1), m.group(2).replace("-", " ").replace("_", " ")
        # 模式: 01-black-lace-finale
        m = re.match(r"(\d{1,3})[-_](.+)", stem)
        if m:
            return m.group(1), m.group(2).replace("-", " ").replace("_", " ")
        return "", ""

    def _match_keywords(self, text: str, keyword_map: dict) -> list:
        """在文本中匹配关键词，返回匹配的 taxonomy 值列表"""
        results = []
        for keyword, value in keyword_map.items():
            if keyword in text:
                results.append(value)
        return results

    def _detect_colors(self, stem: str) -> list:
        """从文件名检测颜色"""
        colors = []
        for keyword, color in self.COLOR_MAP.items():
            if keyword in stem:
                colors.append(color)
        return colors


# ── ================================================================ ──
#  主流程
# ── ================================================================ ──

def generate_thumbnails(input_path: Path, output_dir: Path) -> dict:
    """生成三档缩略图，返回 {variant: path}"""
    if not THUMB_AVAILABLE:
        print("  [warn]  Pillow 未安装，跳过缩略图生成")
        return {}

    img = Image.open(input_path)
    img = img.convert("RGB")

    w, h = img.size
    results = {}

    variants = [
        ("preview", 1600, "webp"),
        ("thumb", 512, "webp"),
        ("tiny", 128, "jpg"),
    ]

    quality = int(os.getenv("THUMBNAIL_QUALITY", "85"))
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

        save_kwargs = {"format": {"webp": "WEBP", "jpg": "JPEG", "png": "PNG"}.get(fmt, fmt.upper()), "quality": quality}
        if fmt == "jpg":
            save_kwargs["optimize"] = True

        resized.save(str(out_path), **save_kwargs)
        results[variant] = out_path
        print(f"    [thumb] {variant}: {out_path.name} ({out_path.stat().st_size // 1024} KB)")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="智能导入生图：自动分类 → COS 上传 → 缩略图 → 索引记录"
    )
    parser.add_argument("--input-dir", default=None,
                        help="输入目录（默认: projects/face/）")
    parser.add_argument("--series", default=None,
                        help="强制指定系列名（覆盖自动检测）")
    parser.add_argument("--type", default="generated", choices=["generated", "reference"],
                        help="图片类型（默认 generated）")
    parser.add_argument("--non-interactive", action="store_true",
                        help="非交互模式，自动处理所有文件")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览模式：只扫描不实际上传")
    parser.add_argument("--no-thumb", action="store_true",
                        help="跳过缩略图生成")
    parser.add_argument("--sync-onedrive", action="store_true",
                        help="处理后复制一份到 OneDrive 备份")
    parser.add_argument("--keep-originals", action="store_true",
                        help="处理后不移动文件（保留在 face/）")
    args = parser.parse_args()

    # ── 定位目录 ─────────────────────────────────────────────────────
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent

    if args.input_dir:
        face_dir = Path(args.input_dir)
    else:
        face_dir = project_dir / "face"

    if not face_dir.exists():
        print(f"错误: 输入目录不存在: {face_dir}", file=sys.stderr)
        sys.exit(1)

    processed_dir = face_dir / ".processed"
    thumb_dir = project_dir / "local_cache" / "face-thumbs"
    index_path = project_dir / "data" / "metadata" / "image-index.jsonl"

    # ── 扫描图片 ─────────────────────────────────────────────────────
    # 处理所有子目录中的图片，也处理 face/ 根目录的图片
    images: list[Path] = []
    for item in face_dir.rglob("*"):
        if item.is_file() and is_image(item):
            # 跳过 .processed 目录
            if ".processed" in item.parts:
                continue
            images.append(item)

    if not images:
        print(f"[camera]  没有发现新图片: {face_dir}")
        return

    images.sort()
    print(f"[camera]  发现 {len(images)} 张图片\n")

    # ── 加载现有 hash（去重）──────────────────────────────────────────
    existing_hashes = load_existing_hashes(str(index_path))

    # ── 初始化分类引擎 ────────────────────────────────────────────────
    classifier = ImageClassifier()

    # ── COS 客户端 ────────────────────────────────────────────────────
    client = None
    if not args.dry_run:
        if not COS_AVAILABLE:
            print("[warn]  cos-python-sdk-v5 未安装，请先安装: pip install cos-python-sdk-v5")
            sys.exit(1)
        client = get_cos_client()
        bucket = COS_BUCKET_GEN if args.type == "generated" else COS_BUCKET_REF
    else:
        bucket = "(dry-run)"

    # ── 处理每张图片 ──────────────────────────────────────────────────
    uploaded = 0
    skipped = 0
    errors = 0
    dt_now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_compact = datetime.now().strftime("%Y%m%d")

    for img_path in images:
        print(f"─── {img_path.name} ───")

        # 1. 计算 hash
        file_hash = sha256_file(str(img_path))
        hash_short = file_hash[:6]

        # 2. 去重检查
        if file_hash in existing_hashes:
            print(f"  [skip]  跳过（已在索引中）: {file_hash[:12]}...")
            skipped += 1
            continue

        # 3. 智能分类
        info = classifier.classify(img_path, project_dir)

        # 如果命令行指定了系列名，覆盖自动检测
        if args.series:
            info["series"] = args.series
            info["series_slug"] = args.series.lower().replace(" ", "-").replace("_", "-")

        # 非交互模式直接使用自动分类结果
        if not args.non_interactive:
            print(f"  [分类]  系列: {info['series']}")
            print(f"          主题: {', '.join(info['themes']) if info['themes'] else '(未匹配)'}")
            print(f"          廓形: {', '.join(info['silhouette']) if info['silhouette'] else '(未匹配)'}")
            print(f"          面料: {', '.join(info['fabric']) if info['fabric'] else '(未匹配)'}")
            print(f"          颜色: {', '.join(info['color']) if info['color'] else '(未匹配)'}")
            print(f"          场景: {', '.join(info['scene']) if info['scene'] else '(未匹配)'}")
            print(f"          备注: {info['notes']}")
            try:
                resp = input("  [确认]  继续？(Y/n/c=自定义) ").strip().lower()
                if resp == "n":
                    print(f"  [skip]  跳过: {img_path.name}")
                    skipped += 1
                    continue
                elif resp == "c":
                    print("  请输入自定义信息（留空保持自动值）:")
                    s = input(f"    系列 [{info['series']}]: ").strip()
                    if s:
                        info["series"] = s
                        info["series_slug"] = s.lower().replace(" ", "-").replace("_", "-")
                    n = input(f"    备注 [{info['notes']}]: ").strip()
                    if n:
                        info["notes"] = n
            except (EOFError, KeyboardInterrupt):
                print("\n  跳过")
                continue

        # 4. 构建 COS 路径
        series_slug = info["series_slug"]
        stem = img_path.stem
        ext = img_path.suffix

        # COS key: gen/face/{series}/{date}/original/{filename}
        cos_base = f"gen/face/{series_slug}/{date_str}"
        cos_key_original = f"{cos_base}/original/{date_compact}_{series_slug}_{stem}{ext}"

        # 5. 上传原图
        cos_url = ""
        if not args.dry_run:
            try:
                print(f"  [up]   上传原图: {bucket}/{cos_key_original} ...")
                with open(str(img_path), "rb") as fp:
                    client.put_object(Bucket=bucket, Body=fp, Key=cos_key_original)
                cos_url = f"cos://{bucket}/{cos_key_original}"
                print(f"  [ok]   {cos_url}")
            except Exception as e:
                print(f"  [err]  上传失败: {e}", file=sys.stderr)
                errors += 1
                continue
        else:
            cos_url = f"cos://{bucket}/{cos_key_original} (dry-run)"
            print(f"  [dry]  DRY RUN: 跳过上传 {cos_key_original}")

        # 6. 生成缩略图并上传
        thumb_urls = {}
        if not args.no_thumb:
            thumbs = generate_thumbnails(img_path, thumb_dir)

            if thumbs and not args.dry_run:
                for variant, thumb_path in thumbs.items():
                    cos_key_thumb = f"{cos_base}/{variant}/{date_compact}_{series_slug}_{stem}__{variant}.{thumb_path.suffix}"
                    try:
                        with open(str(thumb_path), "rb") as fp:
                            client.put_object(Bucket=bucket, Body=fp, Key=cos_key_thumb)
                        thumb_urls[variant] = f"cos://{bucket}/{cos_key_thumb}"
                        print(f"    [up]  {variant}: {cos_key_thumb}")
                    except Exception as e:
                        print(f"    [warn]  缩略图上传失败: {e}")

        # 7. 构建 metadata
        asset_id = generate_asset_id("gen", date_compact, hash_short)

        entry = {
            "asset_id": asset_id,
            "type": args.type,
            "project": "AI Fashion Director",
            "series": info["series"],
            "look": info["look"],
            "look_id": info["look_id"],
            "category": info["category"],
            "themes": info["themes"],
            "silhouette": info["silhouette"],
            "fabric": info["fabric"],
            "color": info["color"],
            "scene": info["scene"],
            "source_url": "",
            "source_domain": "local_generated",
            "collected_at": dt_now,
            "license_status": "self_generated",
            "usage_scope": "commercial_design",
            "do_not_publish": False,
            "image_file": cos_url,
            "thumbnail": thumb_urls,
            "quality_score": info["rating"],
            "notes": info["notes"],
            "created_at": dt_now,
            "sha256": file_hash,
            "import_batch": date_compact,
            "import_script": "import_face_gen.py",
        }

        # 8. 写入本地索引
        os.makedirs(os.path.dirname(str(index_path)), exist_ok=True)
        with open(str(index_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"  [meta]  已记录: {asset_id}")

        # 8.5 OneDrive 同步
        if args.sync_onedrive and not args.dry_run:
            onedrive_root = os.path.expanduser("~/OneDrive")
            onedrive_dst = Path(onedrive_root) / "AI-Photo" / "face" / series_slug / date_str
            onedrive_dst.mkdir(parents=True, exist_ok=True)
            onedrive_file = onedrive_dst / img_path.name
            if not onedrive_file.exists():
                import shutil as _sh
                _sh.copy2(str(img_path), str(onedrive_file))
                print(f"  [onedrive]  → {onedrive_file}")

        # 9. 移动已处理文件
        if not args.keep_originals and not args.dry_run:
            processed_dir.mkdir(parents=True, exist_ok=True)
            dest = processed_dir / img_path.name
            if dest.exists():
                dest = processed_dir / f"{hash_short}_{img_path.name}"
            shutil.move(str(img_path), str(dest))
            print(f"  [move]  → {dest.name}")

        existing_hashes.add(file_hash)
        uploaded += 1
        print()

    # ── 报告 ───────────────────────────────────────────────────────────
    print(f"{'='*50}")
    print(f"[done]  处理完成")
    print(f"  上传:   {uploaded}")
    print(f"  跳过:   {skipped}")
    print(f"  错误:   {errors}")
    if args.dry_run:
        print(f"  [info]  这是 DRY RUN，实际未上传")
    print(f"{'='*50}")

    # 清理临时缩略图
    if thumb_dir.exists() and not args.dry_run:
        shutil.rmtree(thumb_dir, ignore_errors=True)


if __name__ == "__main__":
    main()


