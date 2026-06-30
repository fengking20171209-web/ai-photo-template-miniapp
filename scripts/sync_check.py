import json, hashlib, os

src_root = r"D:\Projects\ai-photo-template-miniapp"
dst_root = r"E:\BaiduNetdiskDownload\百度网盘同步文件\BaiduSyncdisk\个人资料\2025年12月海南自贸岛封关（Hermes）\Codex生图小程序开发项目\ai-photo-template-miniapp"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

key_files = [
    "public/index.html", "public/app.js", "public/styles.css", "public/utils.js",
    "backend/main.py", "backend/routers/templates.py", "backend/routers/cos_serve.py",
    ".env", "TODO.md", "package.json",
    "backend/services/sense_image.py", "backend/routers/image_gen.py",
]

print("=== 关键文件差异检查 ===")
different = []
for f in key_files:
    src = os.path.join(src_root, f)
    dst = os.path.join(dst_root, f)
    if not os.path.exists(src) or not os.path.exists(dst):
        print(f"  {f:40s} MISSING")
        continue
    src_sha = sha256_file(src)
    dst_sha = sha256_file(dst)
    src_size = os.path.getsize(src)
    dst_size = os.path.getsize(dst)
    same = src_sha == dst_sha
    if not same:
        different.append(f)
    status = "OK" if same else "DIFF"
    print(f"  {f:40s} {src_size:>6}B vs {dst_size:>6}B  [{status}]")

# Show recent sync log
log_dir = os.path.join(src_root, "logs")
if os.path.exists(log_dir):
    logs = sorted([f for f in os.listdir(log_dir) if f.startswith("sync-")])
    if logs:
        last_log = os.path.join(log_dir, logs[-1])
        print(f"\n最后同步: {logs[-1]}")
        with open(last_log, "r") as f:
            content = f.read()
        # Show last few lines
        lines = content.strip().split("\n")
        for l in lines[-5:]:
            print(f"  {l}")

if different:
    print(f"\n差异文件 ({len(different)}):")
    for f in different:
        print(f"  {f}")
else:
    print("\n结论: 所有关键文件完全一致")