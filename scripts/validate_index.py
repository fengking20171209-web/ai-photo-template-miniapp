#!/usr/bin/env python3
"""validate_index.py — image-index.jsonl 索引质量检查器 (V2.1)"""
import argparse, json, os, sys
from collections import Counter
from pathlib import Path
from datetime import datetime

SEARCH_PATHS = ["data/metadata/image-index.jsonl","data/image-index.jsonl","image-index.jsonl"]

def find_index(path):
    if path: return path if os.path.exists(path) else None
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    for rel in SEARCH_PATHS:
        for base in [project_dir, Path.cwd()]:
            p = base / rel
            if p.exists(): return str(p.resolve())
    return None

def load_index(path):
    entries, bad_lines = [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                if isinstance(entry, dict): entries.append(entry)
                else: bad_lines.append(lineno)
            except json.JSONDecodeError: bad_lines.append(lineno)
    return entries, bad_lines

def count_empty(entries, fields):
    result = {}
    for f in fields:
        empty = sum(1 for e in entries if e.get(f) is None or e.get(f) == "" or (isinstance(e.get(f), list) and not e.get(f)))
        result[f] = empty
    return result

def validate_index(path, fix=False):
    entries, bad_lines = load_index(path)
    total = len(entries) + len(bad_lines)
    total_valid = len(entries)
    total_invalid = len(bad_lines)

    seen_aid = Counter(e.get("asset_id","") for e in entries if e.get("asset_id"))
    dup_aid = [k for k,v in seen_aid.items() if v > 1]
    missing_aid = sum(1 for e in entries if not e.get("asset_id"))
    seen_hash = Counter(e.get("sha256","") for e in entries if e.get("sha256"))
    dup_hash = [k for k,v in seen_hash.items() if v > 1]

    empty = count_empty(entries, ["series","themes","color","fabric","scene","silhouette","image_file","notes"])

    has_thumb = sum(1 for e in entries if e.get("thumbnail") and isinstance(e.get("thumbnail"), dict) and any(e["thumbnail"].values()))
    missing_thumb = total_valid - has_thumb

    bad_cos = sum(1 for e in entries if e.get("image_file","") and not e["image_file"].startswith("cos://") and not e["image_file"].startswith("http") and e["image_file"] != "(dry-run)")

    score = max(0, min(100, round(100.0 - total_invalid*10 - len(dup_aid)*5 - len(dup_hash)*3 - missing_aid*2 - empty["series"]*3 - empty["themes"] - empty["scene"] - empty["color"] - empty["fabric"] - missing_thumb*2 - bad_cos*2, 1)))

    result = {"index_path":path,"total_records":total,"valid_records":total_valid,"invalid_records":total_invalid,"duplicate_asset_ids":len(dup_aid),"duplicate_sha256":len(dup_hash),"missing_asset_ids":missing_aid,"missing_thumbnails":missing_thumb,"has_thumbnails":has_thumb,"bad_cos_paths":bad_cos,"empty_fields":{k:{"count":v,"pct":round(v/max(total_valid,1)*100,1)} for k,v in empty.items()},"quality_score":score,"bad_lines":bad_lines,"dup_asset_id_list":dup_aid[:10]}

    if fix and total_invalid > 0:
        valid_lines = []
        fixed = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            for lineno, line in enumerate(f, 1):
                if lineno in bad_lines:
                    fixed += 1
                    continue
                valid_lines.append(line)
        with open(path, "w", encoding="utf-8-sig") as f:
            f.writelines(valid_lines)
        result["fixed_invalid_lines"] = fixed
        re = validate_index(path, fix=False)
        result["valid_records"] = re["valid_records"]
        result["invalid_records"] = re["invalid_records"]
        result["quality_score"] = re["quality_score"]

    return result

def print_report(r):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    empty = r["empty_fields"]
    q = r["quality_score"]
    label = "Excellent" if q >= 90 else "Good" if q >= 70 else "Fair" if q >= 50 else "Needs work"
    print(f"\n{'='*60}")
    print(f"  Index Validation Report  |  {ts}")
    print(f"{'='*60}")
    print(f"  索引文件:   {r['index_path']}")
    print(f"  Quality:    {q}/100  [{label}]")
    print(f"\n  -- Records --")
    print(f"    Total:      {r['total_records']}")
    print(f"    Valid:      {r['valid_records']}")
    if r['invalid_records']: print(f"    Invalid:    {r['invalid_records']}" + (f"  (fixed {r['fixed_invalid_lines']})" if 'fixed_invalid_lines' in r else ""))
    print(f"    Duplicate asset_id: {r['duplicate_asset_ids']}")
    print(f"    Duplicate sha256:   {r['duplicate_sha256']}")
    print(f"    Missing asset_id:   {r['missing_asset_ids']}")
    print(f"    Bad COS paths:      {r['bad_cos_paths']}")
    print(f"\n  -- Fields --")
    print(f"    {'Field':<20} {'Empty':>6} {'Rate':>8}")
    print(f"    {'-'*20} {'-'*6} {'-'*8}")
    for field in ["series","themes","scene","color","fabric","silhouette","image_file","notes"]:
        info = empty.get(field, {"count":0,"pct":0.0})
        print(f"    {field:<20} {info['count']:>6} {info['pct']:>7}%")
    print(f"\n  -- Thumbnails --")
    print(f"    Has thumbnail:   {r['has_thumbnails']}")
    print(f"    Missing:         {r['missing_thumbnails']}")
    if r["bad_lines"]: print(f"\n  Damaged lines: {r['bad_lines']}")
    if r["dup_asset_id_list"]: print(f"\n  Duplicate asset_ids: {', '.join(r['dup_asset_id_list'][:5])}")
    print(f"\n  -- Suggestions --")
    s = []
    if r["invalid_records"] > 0: s.append(f"  Run --fix to remove {r['invalid_records']} damaged line(s)")
    if r["duplicate_asset_ids"] > 0: s.append("  Check duplicate asset_ids")
    if empty["themes"]["pct"] > 50: s.append(f"  {empty['themes']['pct']}% missing themes")
    if empty["scene"]["pct"] > 50: s.append(f"  {empty['scene']['pct']}% missing scene")
    if r["missing_thumbnails"] > 0 and r["missing_thumbnails"] == r["total_records"]: s.append("  No thumbnails, run generate_thumbnail.py")
    if q >= 90: s.append("  [OK] Index quality sufficient for V3.0")
    for x in s: print(x)
    if not s: print("  [OK] No suggestions")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description="image-index.jsonl quality checker")
    parser.add_argument("--index", help="path to index file")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fix", action="store_true", help="auto-fix: remove damaged lines")
    args = parser.parse_args()
    path = args.index or find_index(None)
    if not path:
        print("[err]  image-index.jsonl not found", file=sys.stderr)
        sys.exit(1)
    try:
        result = validate_index(path, fix=args.fix)
    except FileNotFoundError:
        print(f"[err]  file not found: {path}", file=sys.stderr); sys.exit(1)
    except Exception as e:
        print(f"[err]  validation failed: {e}", file=sys.stderr); sys.exit(1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)

if __name__ == "__main__":
    main()