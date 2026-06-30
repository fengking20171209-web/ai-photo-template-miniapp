import json, os, time

token_path = r"D:\Projects\ai-photo-template-miniapp\onedrive_token.json"
if os.path.exists(token_path):
    with open(token_path, "r") as f:
        token = json.load(f)
    print("Token: FOUND")
    expires = token.get("expires_at", 0)
    if expires > time.time():
        print(f"  Status: VALID (expires in {(expires-time.time())/3600:.1f}h)")
    else:
        print(f"  Status: EXPIRED")
    print(f"  Email: {token.get('email', token.get('account', 'unknown'))}")
else:
    print("Token: NOT FOUND")

# Check progress files
for pf in ["od_progress.txt", "od_cleanup_progress.txt", "od_remaining_progress.txt", "od_scan_report.txt"]:
    path = os.path.join(r"D:\Projects\ai-photo-template-miniapp", pf)
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read()
        print(f"\n=== {pf} ===")
        lines = content.strip().split("\n")
        for l in lines[-10:]:
            print(f"  {l}")