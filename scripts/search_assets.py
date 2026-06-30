#!/usr/bin/env python3
"""search_assets.py — AI 素材资产本地检索工具 (V3.0)

基于 image-index.jsonl 实现字段加权关键词搜索。

用法:
  python scripts/search_assets.py "空姐 酒店 夜景"
  python scripts/search_assets.py "black lace" --limit 20
  python scripts/search_assets.py --series face-portrait
  python scripts/search_assets.py --color black
  python scripts/search_assets.py --theme luxury_gala
  python scripts/search_assets.py --json "空姐"
  python scripts/search_assets.py --stats           # 统计概览
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import html as html_mod

# ── 路径自动探测 ──────────────────────────────────────────────────────

SEARCH_PATHS = [
    "data/metadata/image-index.jsonl",
    "data/image-index.jsonl",
    "image-index.jsonl",
    "logs/image-index.jsonl",
    "ai-assets/image-index.jsonl",
    "../data/metadata/image-index.jsonl",
    "../image-index.jsonl",
]

# ── 中英文关键词映射表 ────────────────────────────────────────────────

ALIASES = {
    # 职业 / 角色
    "空姐": ["airline", "flight_attendant", "cabin_crew", "stewardess"],
    "护士": ["nurse", "medical", "hospital", "scrubs"],
    "医生": ["doctor", "medical"],
    "教师": ["teacher", "professor"],
    "秘书": ["secretary", "office_lady", "administrative"],
    "OL": ["office_lady", "business", "corporate", "office", "professional"],
    "前台": ["receptionist", "front_desk", "concierge"],
    "礼宾": ["concierge", "hotel_concierge", "bellman"],
    "管家": ["butler", "housekeeper", "maid"],
    "女仆": ["maid", "servant"],
    "模特": ["model", "fashion_model", "runway"],
    "演员": ["actress", "actor"],
    "歌手": ["singer", "vocalist"],
    "学生": ["student", "schoolgirl", "campus"],
    "警察": ["police", "officer"],
    "军人": ["military", "soldier", "uniform"],
    "运动员": ["athlete", "sportswoman"],

    # 酒店 / 旅行
    "酒店": ["hotel", "luxury_hotel", "hotel_corridor", "resort"],
    "旅馆": ["hotel", "inn", "lodge"],
    "大堂": ["lobby", "marble_lobby", "hotel_lobby"],
    "走廊": ["corridor", "hotel_corridor", "hallway"],
    "房间": ["room", "suite", "hotel_room", "bedroom"],
    "套房": ["suite", "luxury_suite", "presidential_suite"],
    "泳池": ["pool", "poolside", "swimming_pool", "pool_goddess"],
    "泳装": ["swimwear", "bikini", "swimsuit", "pool"],
    "度假": ["resort", "vacation", "tropical_resort", "holiday"],
    "旅行": ["travel", "trip", "vacation", "journey"],
    "机场": ["airport", "terminal", "boarding"],
    "飞机": ["airplane", "aircraft", "cabin", "flight"],

    # 城市 / 场景
    "夜景": ["night", "tokyo_night", "city_lights", "night_city", "neon"],
    "东京": ["tokyo", "japan", "shibuya", "shinjuku"],
    "上海": ["shanghai", "china", "bund", "pudong"],
    "巴黎": ["paris", "france", "eiffel"],
    "纽约": ["new_york", "nyc", "manhattan", "broadway"],
    "伦敦": ["london", "uk", "britain"],
    "咖啡": ["coffee", "cafe", "cafe_terrace", "coffee_shop"],
    "酒吧": ["bar", "lounge", "lounge_bar", "nightclub"],
    "餐厅": ["restaurant", "dining", "fine_dining"],
    "天台": ["rooftop", "terrace", "rooftop_terrace"],
    "花园": ["garden", "park", "garden_park", "courtyard"],
    "海滩": ["beach", "seaside", "beach_seaside", "coast"],
    "湖边": ["lake", "lakeside", "waterfront"],
    "森林": ["forest", "woods", "nature", "forest_nature"],
    "街道": ["street", "alley", "city_street", "urban"],

    # 颜色
    "黑色": ["black"],
    "白色": ["white", "ivory"],
    "红色": ["red", "crimson", "scarlet"],
    "粉色": ["pink", "rose", "barbie"],
    "绿色": ["green", "emerald", "sage", "jade"],
    "蓝色": ["blue", "navy", "azure"],
    "金色": ["gold", "golden"],
    "银色": ["silver"],
    "紫色": ["purple", "violet", "lavender"],
    "灰色": ["gray", "grey"],
    "棕色": ["brown", "tan", "beige"],
    "黄色": ["yellow"],
    "橙色": ["orange", "coral", "peach"],
    "透明": ["transparent", "sheer", "clear"],

    # 面料 / 材质
    "蕾丝": ["lace", "lace_trim"],
    "丝绸": ["silk", "satin"],
    "缎面": ["satin", "silk"],
    "真丝": ["silk"],
    "雪纺": ["chiffon"],
    "丝绒": ["velvet"],
    "皮革": ["leather"],
    "牛仔": ["denim"],
    "针织": ["knit", "ribbed_knit", "jersey"],
    "网纱": ["mesh", "soft_mesh", "sheer"],
    "毛呢": ["wool", "tweed", "cashmere"],
    "棉": ["cotton", "jersey", "matte"],
    "亮片": ["sequin", "glitter", "sparkle"],
    "皮草": ["fur", "fleece"],

    # 款式 / 廓形
    "旗袍": ["cheongsam", "qipao", "oriental", "oriental_bodycon"],
    "汉服": ["hanfu", "chinese_traditional", "oriental"],
    "古风": ["hanfu", "chinese_traditional", "oriental", "ancient"],
    "肚兜": ["dudou", "dudou_halter", "dudou_modern"],
    "礼服": ["gown", "evening", "gala", "formal"],
    "婚纱": ["bridal", "wedding", "white_lace"],
    "西装": ["suit", "blazer", "business", "corporate"],
    "制服": ["uniform", "corporate", "official"],
    "运动": ["sporty", "active", "sportswear", "athletic"],
    "泳装": ["swimwear", "bikini", "swimsuit"],
    "内衣": ["lingerie", "lace_lingerie", "intimate"],
    "连衣": ["dress", "bodycon", "mini_dress"],
    "短裙": ["skirt", "mini_skirt", "skater_dress"],
    "包臀": ["bodycon", "pencil", "bandage"],
    "高跟": ["heels", "high_heels", "stilettos"],
    "靴": ["boots", "knee_boots", "ankle_boots"],
    "丝袜": ["stockings", "hose", "pantyhose", "nylons"],
    "黑丝": ["black_stockings", "black_hose"],
    "白丝": ["white_stockings", "white_hose"],

    # 风格 / 主题
    "商务": ["business", "corporate", "professional", "office"],
    "时尚": ["fashion", "chic", "stylish", "editorial"],
    "复古": ["retro", "vintage", "y2k", "nostalgic"],
    "未来": ["cyber", "futuristic", "sci_fi", "neon"],
    "哥特": ["gothic", "dark", "mysterious"],
    "简约": ["minimalist", "simple", "clean", "modern"],
    "奢华": ["luxury", "gala", "high_end", "premium"],
    "可爱": ["cute", "sweet", "lovely", "kawaii"],
    "性感": ["sexy", "seductive", "glamorous"],
    "优雅": ["elegant", "graceful", "refined", "classy"],
    "清纯": ["pure", "innocent", "fresh", "natural"],
    "御姐": ["mature", "sophisticated", "glamorous"],
    "甜美": ["sweet", "cute", "girly"],
    "冷淡": ["cold", "aloof", "icy", "distant"],
    "街头": ["street", "urban", "casual", "metro_chic"],
    "文艺": ["literary", "bohemian", "artistic", "coffee"],

    # 常见英文缩写展开
    "cc": ["cc", "cici"],
    "siuf": ["siuf", "siuf_2026"],
}

# ── 字段权重 ──────────────────────────────────────────────────────────

FIELD_WEIGHTS = {
    "themes": 5,
    "series": 4,
    "scene": 4,
    "color": 3,
    "fabric": 3,
    "silhouette": 3,
    "category": 3,
    "tags": 3,
    "notes": 2,
    "look": 2,
    "image_file": 1,
}

# ── 索引加载 ──────────────────────────────────────────────────────────

def find_index() -> str | None:
    """自动探测 image-index.jsonl 路径"""
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    cwd = Path.cwd()

    candidates = []
    for rel in SEARCH_PATHS:
        for base in [project_dir, cwd, script_dir]:
            p = base / rel
            if p not in candidates:
                candidates.append(p)

    for p in candidates:
        if p.exists():
            return str(p.resolve())

    return None


def load_index(path: str) -> list[dict]:
    """加载索引，跳过损坏行"""
    entries = []
    errors = 0
    with open(path, "r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict) and entry.get("asset_id"):
                    entries.append(entry)
            except json.JSONDecodeError:
                errors += 1
                if errors <= 3:
                    print(f"[warn]  第 {lineno} 行 JSON 损坏，已跳过", file=sys.stderr)
    if errors > 3:
        print(f"[warn]  共跳过 {errors} 行损坏数据", file=sys.stderr)
    return entries


# ── 查询解析 ──────────────────────────────────────────────────────────

def expand_query(query: str) -> list[str]:
    """展开中文关键词为英文同义词列表"""
    terms = query.lower().split()
    expanded = set()

    for term in terms:
        expanded.add(term)
        # 中文别名展开
        if term in ALIASES:
            for alias in ALIASES[term]:
                expanded.add(alias.lower())
        # 反向查：有没有别名指向这个 term
        for cn, en_list in ALIASES.items():
            if term in en_list:
                expanded.add(cn.lower())
                for e in en_list:
                    expanded.add(e.lower())

    return list(expanded)


def text_in_entry(entry: dict, term: str) -> bool:
    """检查单条 entry 是否包含某关键词"""
    term_lower = term.lower()
    for key in ["themes", "scene", "fabric", "color", "silhouette", "category", "tags"]:
        values = entry.get(key)
        if isinstance(values, list):
            for v in values:
                if term_lower in str(v).lower():
                    return True
        elif isinstance(values, str):
            if term_lower in values.lower():
                return True

    for key in ["series", "look", "notes", "image_file", "asset_id", "source_url"]:
        v = entry.get(key)
        if isinstance(v, str) and term_lower in v.lower():
            return True

    return False


def score_entry(entry: dict, terms: list[str]) -> float:
    """字段加权打分"""
    score = 0.0
    term_set = set(t.lower() for t in terms)

    for field, weight in FIELD_WEIGHTS.items():
        values = entry.get(field)
        if values is None:
            continue

        # list 字段
        if isinstance(values, list):
            for v in values:
                vs = str(v).lower()
                for t in term_set:
                    if t in vs:
                        score += weight * (1.0 + 0.5 * vs.count(t))
        # string 字段
        elif isinstance(values, str):
            vs = values.lower()
            for t in term_set:
                if t in vs:
                    score += weight * (1.0 + 0.3 * vs.count(t))

    return round(score, 1)


# ── 过滤器 ────────────────────────────────────────────────────────────

def match_filter(entry: dict, field: str, value: str) -> bool:
    """过滤匹配"""
    v = value.lower()
    raw = entry.get(field)

    if isinstance(raw, list):
        return any(v in str(item).lower() for item in raw)
    elif isinstance(raw, str):
        return v in raw.lower()
    return False


# ── 输出 ──────────────────────────────────────────────────────────────

def safe_get(entry: dict, key: str, default="") -> str:
    v = entry.get(key)
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else default
    return str(v) if v else default


def format_output(entry: dict, score: float, show_json: bool) -> str:
    """格式化输出"""
    if show_json:
        out = dict(entry)
        out["_score"] = score
        return json.dumps(out, ensure_ascii=False)

    thumb = entry.get("thumbnail", {})
    if isinstance(thumb, dict):
        thumb_str = thumb.get("thumb", thumb.get("preview", ""))
    elif isinstance(thumb, str):
        thumb_str = thumb
    else:
        thumb_str = ""

    lines = [
        f"[{entry.get('asset_id', '?')}]  score: {score}  ★{entry.get('quality_score', 0)}",
        f"  series:    {safe_get(entry, 'series')}",
        f"  themes:    {safe_get(entry, 'themes')}",
        f"  scene:     {safe_get(entry, 'scene')}",
        f"  color:     {safe_get(entry, 'color')}",
        f"  fabric:    {safe_get(entry, 'fabric')}",
        f"  silhouette:{safe_get(entry, 'silhouette')}",
    ]
    if thumb_str:
        lines.append(f"  thumb:     {thumb_str}")
    lines.append(f"  file:      {safe_get(entry, 'image_file')}")
    notes = safe_get(entry, "notes")
    if notes:
        lines.append(f"  notes:     {notes}")
    return "\n".join(lines)


def print_stats(entries: list[dict]):
    """打印统计信息"""
    total = len(entries)
    if total == 0:
        print("索引为空")
        return

    series_count = defaultdict(int)
    theme_count = defaultdict(int)
    scene_count = defaultdict(int)
    color_count = defaultdict(int)
    type_count = defaultdict(int)

    for e in entries:
        series_count[safe_get(e, "series", "未知")] += 1
        type_count[safe_get(e, "type", "未知")] += 1
        for key, counter in [("themes", theme_count), ("scene", scene_count), ("color", color_count)]:
            vals = e.get(key)
            if isinstance(vals, list):
                for v in vals:
                    if v:
                        counter[v] += 1

    print(f"\n{'='*50}")
    print(f"  素材资产库统计")
    print(f"{'='*50}")
    print(f"  总资产: {total} 条")
    print(f"  类型:   {dict(type_count)}")
    print(f"\n  ── 系列 Top 10 ──")
    for s, c in sorted(series_count.items(), key=lambda x: -x[1])[:10]:
        print(f"    {s}: {c}")
    if theme_count:
        print(f"\n  ── 主题 Top 10 ──")
        for s, c in sorted(theme_count.items(), key=lambda x: -x[1])[:10]:
            print(f"    {s}: {c}")
    if scene_count:
        print(f"\n  ── 场景 Top 10 ──")
        for s, c in sorted(scene_count.items(), key=lambda x: -x[1])[:10]:
            print(f"    {s}: {c}")
    if color_count:
        print(f"\n  ── 颜色 ──")
        for s, c in sorted(color_count.items(), key=lambda x: -x[1]):
            print(f"    {s}: {c}")
    print(f"{'='*50}\n")


# ── 主入口 ────────────────────────────────────────────────────────────


def cos_to_http(cos_url):
    """Convert cos://bucket/key to https://bucket.cos.region.myqcloud.com/key"""
    if not cos_url or not cos_url.startswith("cos://"):
        return cos_url
    try:
        parts = cos_url[6:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        region = os.environ.get("COS_REGION", "ap-shanghai")
        return f"https://{bucket}.cos.{region}.myqcloud.com/{key}"
    except Exception:
        return cos_url

def render_html(scored_results, query, filters, limit, index_path, total_matched):
    """Render search results as HTML page (V3.0)"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shown = min(limit, len(scored_results))
    results = scored_results[:shown]

    filter_desc = []
    if query:
        filter_desc.append("query: " + html_mod.escape(query))
    for k, v in filters.items():
        if v:
            filter_desc.append(k + ": " + html_mod.escape(v))
    filter_str = " | ".join(filter_desc) if filter_desc else "(browse mode)"

    cards = ""
    if not results:
        cards = '<div class="no-results"><p>No matching results.</p><p>Try different keywords or run --stats to see available fields.</p></div>'
    else:
        for score, entry in results:
            aid = html_mod.escape(str(entry.get("asset_id", "?")))
            series = html_mod.escape(str(entry.get("series", "")))
            notes = html_mod.escape(str(entry.get("notes", "")))
            img_file = html_mod.escape(str(entry.get("image_file", "")))
            quality = entry.get("quality_score", 0) or 0
            star_str = chr(9733) * int(quality)
            notes_html = '<div class="notes">' + notes + '</div>' if notes else ""

            # Resolve preview: thumbnail > original image > placeholder
            thumb = entry.get("thumbnail", {})
            thumb_url = ""
            if isinstance(thumb, dict):
                thumb_url = thumb.get("preview", "") or thumb.get("thumb", "") or thumb.get("tiny", "")
            if not thumb_url:
                thumb_url = entry.get("thumbnail_file", entry.get("thumb", ""))
            # Fallback: use original image as preview
            raw_img = str(entry.get("image_file", ""))
            if not thumb_url and raw_img:
                thumb_url = cos_to_http(raw_img)
            thumb_esc = html_mod.escape(str(thumb_url)) if thumb_url else ""

            # Tags
            tags = []
            for field in ["series", "themes", "scene", "color", "fabric", "silhouette"]:
                val = entry.get(field)
                if isinstance(val, list):
                    for v in val:
                        if v:
                            tags.append((field, html_mod.escape(str(v))))
                elif val:
                    tags.append((field, html_mod.escape(str(val))))

            tags_html = ""
            for tag_field, tag_val in tags:
                tags_html += '<span class="tag tag-' + tag_field + '">' + tag_val + '</span> '

            # Preview image
            if thumb_esc:
                thumb_html = '<div class="thumb"><img src="' + thumb_esc + '" alt="' + aid + '" loading="lazy" onerror="this.parentNode.innerHTML=\'<div class=\\\'no-thumb\\\'>Load Error</div>\'" /></div>'
            else:
                thumb_html = '<div class="thumb"><div class="no-thumb">No Preview</div></div>'

            # Original link (convert cos:// to https:// for browser)
            img_http = cos_to_http(raw_img)
            img_esc = html_mod.escape(img_http) if img_http else ""
            link_html = ""
            if img_http:
                link_html = '<a class="link" href="' + img_esc + '" target="_blank" title="Open original">Open Original</a>'

            cards += '<div class="card">' + thumb_html + '<div class="card-body"><div class="card-header"><span class="asset-id">' + aid + '</span><span class="score">score: ' + str(score) + '</span><span class="quality">' + star_str + '</span></div><div class="tags">' + tags_html + '</div>' + notes_html + link_html + '</div></div>'

    page = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>AI Asset Search Results</title>\n<style>\n* { margin:0; padding:0; box-sizing:border-box; }\nbody { background:#1a1a2e; color:#e0e0e0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; padding:24px; }\nheader { max-width:1400px; margin:0 auto 24px; }\nheader h1 { font-size:20px; color:#a78bfa; margin-bottom:8px; }\nheader .meta { font-size:13px; color:#8888aa; }\nheader .meta span { margin-right:16px; }\nheader .filters { margin-top:8px; font-size:12px; color:#6b7280; }\n.grid { max-width:1400px; margin:0 auto; display:grid; grid-template-columns:repeat(auto-fill, minmax(340px, 1fr)); gap:20px; }\n.card { background:#f8f9fa; border-radius:12px; overflow:hidden; color:#1a1a2e; box-shadow:0 2px 12px rgba(0,0,0,0.3); transition:transform 0.15s; }\n.card:hover { transform:translateY(-3px); box-shadow:0 6px 20px rgba(0,0,0,0.4); }\n.thumb { width:100%; height:240px; background:#e5e7eb; display:flex; align-items:center; justify-content:center; overflow:hidden; }\n.thumb img { width:100%; height:100%; object-fit:cover; }\n.no-thumb { color:#9ca3af; font-size:14px; }\n.card-body { padding:16px; }\n.card-header { display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap; }\n.asset-id { font-family:monospace; font-size:12px; color:#6366f1; font-weight:600; }\n.score { font-size:12px; color:#f59e0b; font-weight:600; }\n.quality { color:#f59e0b; font-size:14px; }\n.tags { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px; }\n.tag { display:inline-block; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:500; }\n.tag-series { background:#dbeafe; color:#1e40af; }\n.tag-themes { background:#fce7f3; color:#be185d; }\n.tag-scene { background:#d1fae5; color:#065f46; }\n.tag-color { background:#fef3c7; color:#92400e; }\n.tag-fabric { background:#e0e7ff; color:#3730a3; }\n.tag-silhouette { background:#ede9fe; color:#6d28d9; }\n.notes { font-size:13px; color:#4b5563; margin-top:6px; line-height:1.5; }\n.link { display:inline-block; margin-top:10px; padding:6px 14px; background:#6366f1; color:#fff; border-radius:6px; text-decoration:none; font-size:12px; font-weight:500; }\n.link:hover { background:#4f46e5; }\n.no-results { text-align:center; padding:80px 20px; color:#6b7280; max-width:1400px; margin:0 auto; }\n.no-results p { margin-bottom:8px; }\nfooter { max-width:1400px; margin:32px auto 0; padding-top:16px; border-top:1px solid #2a2a4a; font-size:12px; color:#6b7280; }\nfooter span { margin-right:20px; }\n@media (max-width:600px) { body { padding:12px; } .grid { grid-template-columns:1fr; gap:12px; } .thumb { height:180px; } }\n</style>\n</head>\n<body>\n<header>\n<h1>AI Asset Search Results</h1>\n<div class="meta"><span>Query: ' + html_mod.escape(query if query else "(browse mode)") + '</span><span>Results: ' + str(shown) + '/' + str(total_matched) + '</span><span>Generated: ' + ts + '</span></div>\n<div class="filters">Filters: ' + filter_str + '</div>\n</header>\n<div class="grid">' + cards + '</div>\n<footer><span>Index: ' + html_mod.escape(index_path) + '</span><span>Matched: ' + str(total_matched) + '</span><span>Generated by search_assets.py V3.0</span></footer>\n</body>\n</html>'
    return page


def main():
    parser = argparse.ArgumentParser(
        description="AI 素材资产本地检索工具 (V2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python scripts/search_assets.py "空姐 酒店 夜景"
  python scripts/search_assets.py "black lace" --limit 20
  python scripts/search_assets.py --series face-portrait
  python scripts/search_assets.py --color black --limit 5
  python scripts/search_assets.py --theme luxury_gala --json
  python scripts/search_assets.py --stats
""")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词（空格分隔多词）")
    parser.add_argument("--limit", type=int, default=10, help="输出条数 (默认 10)")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--series", help="按系列过滤")
    parser.add_argument("--theme", help="按主题过滤")
    parser.add_argument("--color", help="按颜色过滤")
    parser.add_argument("--scene", help="按场景过滤")
    parser.add_argument("--fabric", help="按面料过滤")
    parser.add_argument("--stats", action="store_true", help="\u7edf\u8ba1\u6982\u89c8")
    parser.add_argument("--html", action="store_true", help="HTML \u7f51\u9875\u7ed3\u679c\u8f93\u51fa")
    parser.add_argument("--index", help="指定索引文件路径")
    args = parser.parse_args()

    # 找索引
    index_path = args.index or find_index()
    if not index_path:
        print("[err]  未找到 image-index.jsonl", file=sys.stderr)
        print("  尝试: --index /path/to/image-index.jsonl", file=sys.stderr)
        sys.exit(1)

    # 加载
    try:
        entries = load_index(index_path)
    except FileNotFoundError:
        print("[err]  索引文件不存在: " + index_path, file=sys.stderr)
        sys.exit(1)
    if not entries:
        print("[warn]  索引为空或无法读取", file=sys.stderr)
        sys.exit(1)

    if args.stats:
        print_stats(entries)
        return

    # 过滤
    filters_applied = False
    filtered = list(entries)

    if args.series:
        filtered = [e for e in filtered if match_filter(e, "series", args.series)]
        filters_applied = True
    if args.theme:
        filtered = [e for e in filtered if match_filter(e, "themes", args.theme)]
        filters_applied = True
    if args.color:
        filtered = [e for e in filtered if match_filter(e, "color", args.color)]
        filters_applied = True
    if args.scene:
        filtered = [e for e in filtered if match_filter(e, "scene", args.scene)]
        filters_applied = True
    if args.fabric:
        filtered = [e for e in filtered if match_filter(e, "fabric", args.fabric)]
        filters_applied = True

    if not args.query and not filters_applied:
        filtered.sort(key=lambda e: -(e.get("quality_score", 0) or 0))
        browse_results = [(e.get("quality_score", 0) or 0, e) for e in filtered]
        total = len(browse_results)
        shown = min(args.limit, total)

        # HTML output
        if args.html:
            filters_dict = {"series": args.series, "theme": args.theme, "color": args.color, "scene": args.scene, "fabric": args.fabric}
            html_out = render_html(browse_results[:shown], args.query, filters_dict, args.limit, index_path, total)
            out_dir = Path.cwd() / "outputs"
            out_dir.mkdir(exist_ok=True)
            ts_str = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = out_dir / f"search-results-{ts_str}.html"
            out_path.write_text(html_out, encoding="utf-8")
            print(f"[html]  {out_path}")

        print("[info]  \u65e0\u641c\u7d22\u6761\u4ef6\uff0c\u6309 quality_score \u5012\u5e8f\u8f93\u51fa\n")
        for i, (score, e) in enumerate(browse_results[:shown]):
            print(format_output(e, score, args.json))
            if i < shown - 1 and not args.json:
                print()
        if not args.json:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n--- {shown}/{total} \u6761 | {ts} ---")
        return

    # 展开查询
    if args.query:
        terms = expand_query(args.query)
    else:
        terms = []

    # 打分 + 排序
    scored = [(score_entry(e, terms), e) for e in filtered]
    scored.sort(key=lambda x: -x[0])

    # 输出最相关 + 过滤掉 0 分的（如果有搜索词的话）
    if terms:
        scored = [(s, e) for s, e in scored if s > 0]

    if not scored:
        if args.html:
            filters_dict = {"series": args.series, "theme": args.theme, "color": args.color, "scene": args.scene, "fabric": args.fabric}
            html_out = render_html([], args.query, filters_dict, args.limit, index_path, 0)
            out_dir = Path.cwd() / "outputs"
            out_dir.mkdir(exist_ok=True)
            ts_str = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = out_dir / f"search-results-{ts_str}.html"
            out_path.write_text(html_out, encoding="utf-8")
            print(f"[html]  {out_path}")
        print(f"[info]  未找到匹配结果，试试其他关键词")
        print(f"  搜索词: {args.query}")
        print(f"  提示:   可用 --stats 查看可用的主题/场景/颜色")
        return

    total = len(scored)
    shown = min(args.limit, total)
    print(f"[info]  找到 {total} 条结果，展示前 {shown} 条\n")

    for i, (score, entry) in enumerate(scored[:shown]):
        print(format_output(entry, score, args.json))
        if i < shown - 1 and not args.json:
            print()

    # HTML output
    if args.html:
        filters_dict = {"series": args.series, "theme": args.theme, "color": args.color, "scene": args.scene, "fabric": args.fabric}
        html_out = render_html(scored[:shown], args.query, filters_dict, args.limit, index_path, total)
        out_dir = Path.cwd() / "outputs"
        out_dir.mkdir(exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = out_dir / f"search-results-{ts_str}.html"
        out_path.write_text(html_out, encoding="utf-8")
        print(f"[html]  {out_path}")

    # 汇总
    if not args.json:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n--- {shown}/{total} 条 | {ts} ---")


if __name__ == "__main__":
    main()
