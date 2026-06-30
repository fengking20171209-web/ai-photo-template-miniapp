import json, hashlib, os

# Load the image index
with open(r"D:\Projects\ai-photo-template-miniapp\data\metadata\image-index.jsonl", "r", encoding="utf-8-sig") as f:
    index_lines = f.readlines()

# Build SHA map from index
index_shas = set()
for l in index_lines:
    d = json.loads(l)
    sha = d.get("sha256", "")
    if sha:
        index_shas.add(sha)

# Check face files against index
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

print("=== face/ 目录 vs COS 索引 ===")
face_root = r"D:\Projects\ai-photo-template-miniapp\face"
all_uploaded = True
for root, dirs, fnames in os.walk(face_root):
    for f in fnames:
        if not f.endswith((".png", ".jpg", ".jpeg")): continue
        path = os.path.join(root, f)
        sha = sha256_file(path)
        rel = os.path.relpath(path, face_root)
        status = "UPLOADED" if sha in index_shas else "MISSING"
        if status == "MISSING": all_uploaded = False
        print(f"  [{status:9s}] face/{rel}")

print()
if all_uploaded:
    print("结论: face/ 所有图片已在 COS 上 ✅")
else:
    print("结论: 部分图片未上传到 COS")

# Also check total COS stats
print(f"\nCOS 索引总数: {len(index_shas)} 张图片")
series_count = {}
for l in index_lines:
    d = json.loads(l)
    s = d.get("series", "unknown")
    series_count[s] = series_count.get(s, 0) + 1
print("系列分布:")
for s, c in sorted(series_count.items(), key=lambda x: -x[1]):
    print(f"  {s:20s}: {c} 张")