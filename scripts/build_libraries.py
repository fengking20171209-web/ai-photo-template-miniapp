"""Generate the Background & Outfit libraries for the DIY Prompt OS.

No web scraping: data is composed programmatically from a curated taxonomy.
All clothing wording uses fashion / editorial styling language (never explicit).

Outputs:
  public/data/backgrounds.json  (>= 300 items)
  public/data/outfits.json      (>= 500 items)

Data structures (per U4 refined spec):
  Background: {id, name, category[], space[], atmosphere[], lighting[],
               perspective[], prompt_keywords[]}
  Outfit:    {id, name, category[], style_tags[], fabric_tags[],
              fashion_keywords[]}
"""
from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "data"

# --------------------------------------------------------------------------
# BACKGROUNDS
# --------------------------------------------------------------------------
# Each space: (zh, en, scene_category, space_tag)
SPACES = [
    # indoor / luxury
    ("豪华酒店套房", "luxury hotel suite", "室内", "酒店"),
    ("总统套房", "presidential suite", "室内", "酒店"),
    ("现代卧室", "modern bedroom", "室内", "卧室"),
    ("北欧风卧室", "scandinavian bedroom", "室内", "卧室"),
    ("大理石浴室", "marble bathroom", "室内", "浴室"),
    ("简约客厅", "minimalist living room", "室内", "客厅"),
    ("复古书房", "vintage study room", "室内", "书房"),
    ("开放式厨房", "open kitchen", "室内", "厨房"),
    ("工业风咖啡馆", "industrial cafe interior", "室内", "咖啡馆"),
    ("独立书店", "cozy bookstore", "室内", "书店"),
    ("现代美术馆", "modern art gallery", "室内", "美术馆"),
    ("白色无缝影棚", "white cyclorama studio", "室内", "影棚"),
    ("灰调摄影影棚", "grey photography studio", "室内", "影棚"),
    ("暗色调影棚", "dark moody studio", "室内", "影棚"),
    ("现代办公室", "modern office interior", "室内", "办公室"),
    ("健身房", "modern gym interior", "室内", "健身房"),
    ("舞蹈教室", "dance studio with mirrors", "室内", "舞蹈室"),
    ("鸡尾酒吧", "stylish cocktail bar", "室内", "酒吧"),
    ("高级餐厅", "fine dining restaurant", "室内", "餐厅"),
    ("室内泳池", "indoor swimming pool", "室内", "泳池"),
    ("玻璃温室", "glass greenhouse", "室内", "温室"),
    ("宏伟图书馆", "grand library hall", "室内", "图书馆"),
    ("复古唱片店", "vintage record store", "室内", "店铺"),
    ("loft 公寓", "industrial loft apartment", "室内", "公寓"),
    ("茶室", "japanese tea room", "室内", "茶室"),
    # urban / outdoor
    ("城市天台", "city rooftop at", "城市", "天台"),
    ("霓虹街道", "neon-lit street", "城市", "街道"),
    ("老城街巷", "old town narrow alley", "城市", "街巷"),
    ("摩天楼群", "skyscraper district", "城市", "高楼"),
    ("人行天桥", "pedestrian overpass", "城市", "天桥"),
    ("涂鸦墙街区", "graffiti wall street", "城市", "街区"),
    ("繁华商业街", "busy shopping street", "城市", "商业街"),
    ("复古地铁站", "retro subway station", "城市", "地铁站"),
    ("机场候机厅", "airport terminal", "城市", "机场"),
    ("海港码头", "harbor dock", "城市", "码头"),
    ("游艇甲板", "luxury yacht deck", "城市", "游艇"),
    ("天台游泳池", "rooftop infinity pool", "城市", "泳池"),
    # nature
    ("海边沙滩", "seaside sandy beach", "自然", "海边"),
    ("海边悬崖", "coastal cliff", "自然", "海边"),
    ("花园庭院", "garden courtyard", "自然", "花园"),
    ("樱花小径", "cherry blossom path", "自然", "花园"),
    ("枫叶林", "autumn maple forest", "自然", "森林"),
    ("竹林小道", "bamboo grove path", "自然", "森林"),
    ("薰衣草田", "lavender field", "自然", "花田"),
    ("向日葵田", "sunflower field", "自然", "花田"),
    ("雪山脚下", "foot of a snowy mountain", "自然", "雪景"),
    ("雪后街道", "snow-covered street", "自然", "雪景"),
    ("雨后街道", "rain-soaked street", "自然", "雨天"),
    ("沙漠沙丘", "desert sand dunes", "自然", "沙漠"),
    ("辽阔草原", "open grassland plains", "自然", "草原"),
    ("森林小径", "misty forest trail", "自然", "森林"),
    ("静谧湖边", "tranquil lakeside", "自然", "湖边"),
    ("古镇水乡", "ancient water town", "自然", "水乡"),
    ("开阔公路", "open desert highway", "自然", "公路"),
    ("葡萄园", "vineyard rows", "自然", "葡萄园"),
]

# (zh, en_fragment, atmosphere_tag)
LIGHT_COMBOS = [
    ("黄昏暖光", "golden hour, warm sunset light", "温暖"),
    ("清晨柔光", "soft morning light", "清新"),
    ("正午自然光", "bright midday natural light", "自然"),
    ("夜晚霓虹", "night neon lights", "霓虹"),
    ("室内暖光", "warm ambient indoor light", "温暖"),
    ("冷调蓝光", "cool blue tone lighting", "冷感"),
    ("电影感打光", "cinematic dramatic lighting", "电影感"),
    ("逆光剪影", "backlight rim light", "氛围感"),
]

# (zh, en)
PERSPECTIVES = [
    ("特写", "close-up framing"),
    ("半身中景", "medium half-body shot"),
    ("全身远景", "full-body wide shot"),
    ("广角环境", "wide-angle environmental shot"),
    ("俯视", "high-angle view"),
    ("仰视", "low-angle view"),
]


def build_backgrounds() -> list[dict]:
    items: list[dict] = []
    n = 0
    for s_zh, s_en, scene, space_tag in SPACES:
        for i, (l_zh, l_en, atmo) in enumerate(LIGHT_COMBOS):
            p_zh, p_en = PERSPECTIVES[(n) % len(PERSPECTIVES)]
            n += 1
            items.append({
                "id": f"bg_{n:03d}",
                "name": f"{s_zh} · {l_zh}",
                "category": [scene, space_tag],
                "space": [space_tag],
                "atmosphere": [atmo],
                "lighting": [l_zh],
                "perspective": [p_zh],
                "prompt_keywords": [s_en, l_en, f"{p_en}"],
            })
    return items


# --------------------------------------------------------------------------
# OUTFITS
# --------------------------------------------------------------------------
# (zh, en, category, [style_tags], [fabric_tags])
GARMENTS = [
    # 日常 / casual
    ("牛仔外套搭配T恤", "denim jacket with t-shirt", "日常", ["休闲", "街头"], ["牛仔", "棉质"]),
    ("oversize 卫衣", "oversized hoodie", "日常", ["休闲", "街头"], ["棉质"]),
    ("针织开衫", "knit cardigan", "日常", ["休闲", "甜美"], ["针织"]),
    ("休闲风衣", "casual trench coat", "日常", ["休闲", "优雅"], ["风衣布"]),
    ("法式衬衫", "french blouse", "日常", ["优雅", "清纯"], ["棉质"]),
    ("毛衣配半裙", "sweater with skirt", "日常", ["甜美", "清纯"], ["针织"]),
    ("工装连体裤", "utility jumpsuit", "日常", ["街头", "中性"], ["棉质"]),
    ("背带裤", "overall dungarees", "日常", ["可爱", "休闲"], ["牛仔"]),
    # 连衣裙 / dress
    ("碎花连衣裙", "floral midi dress", "连衣裙", ["甜美", "清新"], ["雪纺"]),
    ("真丝吊带裙", "silk slip dress", "连衣裙", ["优雅", "性感"], ["真丝"]),
    ("缎面长裙", "satin maxi dress", "连衣裙", ["优雅", "成熟"], ["缎面"]),
    ("小黑裙", "little black dress", "连衣裙", ["优雅", "成熟"], ["针织"]),
    ("针织连衣裙", "knit bodycon dress", "连衣裙", ["御姐", "成熟"], ["针织"]),
    ("蕾丝连衣裙", "lace detail dress", "连衣裙", ["优雅", "性感"], ["蕾丝"]),
    ("波点复古裙", "polka dot retro dress", "连衣裙", ["复古", "甜美"], ["棉质"]),
    ("白色长裙", "flowing white dress", "连衣裙", ["清纯", "梦幻"], ["雪纺"]),
    # 礼服 / evening
    ("晚礼服", "evening gown", "礼服", ["优雅", "成熟"], ["缎面"]),
    ("鱼尾礼服", "mermaid evening gown", "礼服", ["优雅", "性感"], ["缎面"]),
    ("亮片礼服", "sequin gown", "礼服", ["派对", "华丽"], ["亮片"]),
    ("丝绒礼服", "velvet evening dress", "礼服", ["复古", "成熟"], ["丝绒"]),
    ("一字肩礼服", "off-shoulder gown", "礼服", ["优雅", "性感"], ["缎面"]),
    # 职业 / business
    ("职业西装套装", "tailored suit set", "职业装", ["御姐", "成熟"], ["西装料"]),
    ("阔腿裤套装", "wide-leg trouser suit", "职业装", ["中性", "成熟"], ["西装料"]),
    ("衬衫配铅笔裙", "shirt with pencil skirt", "职业装", ["成熟", "御姐"], ["棉质"]),
    ("西装连衣裙", "blazer dress", "职业装", ["御姐", "中性"], ["西装料"]),
    # 街头 / streetwear
    ("机能风外套", "techwear jacket", "街头", ["街头", "未来"], ["机能面料"]),
    ("皮夹克", "leather biker jacket", "街头", ["街头", "酷感"], ["皮革"]),
    ("运动套装", "athleisure tracksuit", "运动", ["运动", "活力"], ["针织"]),
    ("瑜伽运动服", "yoga activewear set", "运动", ["运动", "活力"], ["弹力面料"]),
    ("骑行服", "cycling outfit", "运动", ["运动", "中性"], ["弹力面料"]),
    # 制服 / uniform-style fashion
    ("学院风 JK 制服", "preppy school-uniform fashion", "制服", ["学院", "清纯"], ["棉质"]),
    ("水手服时装", "sailor-collar fashion outfit", "制服", ["学院", "可爱"], ["棉质"]),
    ("空乘制服时装", "flight-attendant inspired fashion", "制服", ["职业", "优雅"], ["西装料"]),
    ("护士风时装", "nurse-inspired fashion costume", "制服", ["职业", "可爱"], ["棉质"]),
    # 主题装扮 / stylized fashion (editorial framing, non-explicit)
    ("兔女郎风时装", "bunny-inspired fashion bodysuit, editorial costume", "主题装扮", ["派对", "复古"], ["缎面"]),
    ("女仆风时装", "maid-inspired ruffled fashion dress, editorial costume", "主题装扮", ["可爱", "复古"], ["棉质"]),
    ("洛丽塔时装", "lolita fashion dress", "主题装扮", ["甜美", "梦幻"], ["蕾丝"]),
    ("赛博朋克造型", "cyberpunk-styled fashion outfit", "Cosplay", ["未来", "街头"], ["机能面料"]),
    ("旗袍改良时装", "modern qipao-inspired fashion", "主题装扮", ["复古", "优雅"], ["真丝"]),
    ("和风浴衣时装", "yukata-inspired fashion", "主题装扮", ["复古", "清新"], ["棉质"]),
    # 内衣风时装 / lingerie-inspired fashion (editorial, non-explicit)
    ("蕾丝内衣风造型", "lingerie-inspired fashion, lace detailing, editorial styling", "内衣风", ["性感", "优雅"], ["蕾丝"]),
    ("缎面睡裙造型", "satin slip loungewear, editorial styling", "内衣风", ["优雅", "性感"], ["缎面"]),
    ("透视纱质造型", "editorial sheer fabric styling, layered tulle", "内衣风", ["性感", "梦幻"], ["纱质"]),
    ("高级内衣美学造型", "high-fashion intimate wear aesthetic, editorial", "内衣风", ["性感", "成熟"], ["蕾丝"]),
    # 泳装 / swimwear
    ("连体泳衣", "one-piece swimsuit fashion", "泳装", ["运动", "性感"], ["弹力面料"]),
    ("比基尼时装", "bikini fashion editorial", "泳装", ["性感", "活力"], ["弹力面料"]),
    ("沙滩罩衫", "beach cover-up dress", "泳装", ["清新", "度假"], ["雪纺"]),
    # 上衣下装 separates
    ("吊带背心配牛仔裤", "cami top with jeans", "日常", ["休闲", "性感"], ["牛仔"]),
    ("露肩上衣配短裙", "off-shoulder top with mini skirt", "派对", ["甜美", "性感"], ["针织"]),
    ("衬衫配西装短裤", "shirt with tailored shorts", "日常", ["中性", "优雅"], ["棉质"]),
    ("毛呢大衣套装", "wool coat ensemble", "日常", ["成熟", "优雅"], ["毛呢"]),
]

# (zh, en)
COLORS = [
    ("白色", "white"),
    ("黑色", "black"),
    ("红色", "red"),
    ("酒红色", "burgundy"),
    ("藏蓝色", "navy blue"),
    ("粉色", "soft pink"),
    ("浅紫色", "lavender"),
    ("米色", "beige"),
    ("墨绿色", "emerald green"),
    ("香槟金", "champagne gold"),
]


def build_outfits() -> list[dict]:
    items: list[dict] = []
    n = 0
    for g_zh, g_en, cat, styles, fabrics in GARMENTS:
        for c_zh, c_en in COLORS:
            n += 1
            kws = [f"{c_en} {g_en}"]
            kws += [_fabric_en(f) for f in fabrics]
            kws.append("editorial fashion photography")
            items.append({
                "id": f"cl_{n:03d}",
                "name": f"{c_zh}{g_zh}",
                "category": [cat],
                "style_tags": styles,
                "fabric_tags": fabrics,
                "fashion_keywords": kws,
            })
    return items


_FABRIC_EN = {
    "牛仔": "denim", "棉质": "cotton", "针织": "knit", "风衣布": "gabardine",
    "雪纺": "chiffon", "真丝": "silk", "缎面": "satin", "蕾丝": "lace fabric",
    "丝绒": "velvet", "亮片": "sequin", "西装料": "tailored wool", "皮革": "leather",
    "机能面料": "technical fabric", "弹力面料": "stretch fabric", "纱质": "sheer tulle",
    "毛呢": "wool tweed",
}


def _fabric_en(zh: str) -> str:
    return _FABRIC_EN.get(zh, zh)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backgrounds = build_backgrounds()
    outfits = build_outfits()
    (OUT_DIR / "backgrounds.json").write_text(
        json.dumps(backgrounds, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (OUT_DIR / "outfits.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"backgrounds: {len(backgrounds)}  outfits: {len(outfits)}")


if __name__ == "__main__":
    main()
