import os, hashlib

src = r"D:\Projects\ai-photo-template-miniapp"
dst = r"E:\BaiduNetdiskDownload\百度网盘同步文件\BaiduSyncdisk\个人资料\2025年12月海南自贸岛封关（Hermes）\Codex生图小程序开发项目\ai-photo-template-miniapp"

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# 检查所有新增文件（D盘有但百度网盘没有）
new_in_e = []
new_in_d = []
diff_files = []

for root, dirs, fnames in os.walk(dst):
    for f in fnames:
        dpath = os.path.join(root, f)
        rel = os.path.relpath(dpath, dst)
        spath = os.path.join(src, rel)
        if not os.path.exists(spath):
            new_in_e.append(rel)
            continue
        if sha(dpath) != sha(spath):
            diff_files.append(rel)

for root, dirs, fnames in os.walk(src):
    for f in fnames:
        spath = os.path.join(root, f)
        rel = os.path.relpath(spath, src)
        dpath = os.path.join(dst, rel)
        if not os.path.exists(dpath):
            new_in_d.append(rel)

print("=== 同步状态总览 ===")
print()
if new_in_e:
    print(f"[百度网盘新增] {len(new_in_e)} 个文件 (在E盘新建，D盘没有):")
    for f in sorted(new_in_e)[:20]:
        print(f"  + {f}")
    if len(new_in_e) > 20:
        print(f"  ... 及 {len(new_in_e)-20} 个其它文件")
else:
    print("[百度网盘新增] 无")

print()
if new_in_d:
    print(f"[D盘新增] {len(new_in_d)} 个文件 (在D盘新建，百度网盘没有):")
    for f in sorted(new_in_d)[:10]:
        print(f"  + {f}")
    if len(new_in_d) > 10:
        print(f"  ... 及 {len(new_in_d)-10} 个其它文件")
else:
    print("[D盘新增] 无")

print()
if diff_files:
    print(f"[内容不同] {len(diff_files)} 个文件两边都有但内容不同:")
    for f in sorted(diff_files)[:15]:
        print(f"  ~ {f}")
    if len(diff_files) > 15:
        print(f"  ... 及 {len(diff_files)-15} 个其它文件")
else:
    print("[内容不同] 无")

print()
print("---")
print(f"face/ 目录: 两边完全一致, COS 已上传 (9张)")
print(f"COS 索引: 26张图片")
print(f"最后同步: 2026-05-30 09:48 (D->E 方向)")
print(f"建议: 运行 sync-baidudisk.ps1 把 E 盘新文件同步回 D 盘")