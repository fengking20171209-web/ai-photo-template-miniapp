# Check OneDrive auth token
import json

# Token file
token_path = r"D:\Projects\ai-photo-template-miniapp\onedrive_token.json"
if os.path.exists(token_path):
    with open(token_path, "r") as f:
        token = json.load(f)
    print(f"OneDrive token: exists")
    # Check expiry
    import time
    expires = token.get("expires_at", 0)
    now = time.time()
    if expires > now:
        print(f"  Status: VALID (expires in {(expires-now)/3600:.1f} hours)")
    else:
        print(f"  Status: EXPIRED (expired {now - expires:.0f} seconds ago)")
    print(f"  Email: {token.get('email', 'unknown')}")
else:
    print("OneDrive token: NOT FOUND")

import os

# Check progress
progress_path = r"D:\Projects\ai-photo-template-miniapp\od_progress.txt"
if os.path.exists(progress_path):
    with open(progress_path, "r") as f:
        print(f"\nProgress:\n{f.read()}")

# Check cleanup progress
cleanup_path = r"D:\Projects\ai-photo-template-miniapp\od_cleanup_progress.txt"
if os.path.exists(cleanup_path):
    with open(cleanup_path, "r") as f:
        print(f"\nCleanup progress:\n{f.read()}")

# Check remaining progress
remaining_path = r"D:\Projects\ai-photo-template-miniapp\od_remaining_progress.txt"
if os.path.exists(remaining_path):
    with open(remaining_path, "r") as f:
        print(f"Remaining progress:\n{f.read()}")