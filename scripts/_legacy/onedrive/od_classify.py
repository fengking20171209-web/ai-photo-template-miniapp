import json, requests, os, sys, time, io, cv2, numpy as np
from datetime import datetime

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
IMAGES_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_images.json"

with open(TOKEN_FILE) as f:
    token = json.load(f)
with open(IMAGES_FILE, encoding="utf-8") as f:
    all_images = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}

# Load face cascade
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

total = len(all_images)
to_delete = []
to_keep = []
errors = []
start_time = time.time()

print(f"Classifying {total} images via face detection...")
print(f"0/{total} (0%) | Elapsed: 0s | Est: --")

for i, img in enumerate(all_images):
    img_id = img["id"]
    img_name = img["name"]
    has_face = False
    
    try:
        # Download thumbnail (small, fast)
        thumb_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/thumbnails/0/small/content"
        resp = requests.get(thumb_url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            img_arr = np.frombuffer(resp.content, np.uint8)
            img_cv = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if img_cv is not None:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                has_face = len(faces) > 0
        else:
            # Fallback: try direct image download
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{img_id}/content"
            resp2 = requests.get(url, headers=headers, timeout=30)
            if resp2.status_code == 200:
                img_arr = np.frombuffer(resp2.content, np.uint8)
                img_cv = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                if img_cv is not None:
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                    has_face = len(faces) > 0
            
    except Exception as e:
        errors.append({"id": img_id, "name": img_name, "error": str(e)})
        continue
    
    if has_face:
        to_keep.append(img)
    else:
        to_delete.append(img)
    
    # Progress update every 50 images
    if (i + 1) % 50 == 0 or i == total - 1:
        elapsed = time.time() - start_time
        pct = (i + 1) / total * 100
        if i > 0:
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate
            est_str = f"{int(remaining // 60)}m{int(remaining % 60)}s"
        else:
            est_str = "--"
        print(f"{i+1}/{total} ({pct:.0f}%) | Elapsed: {int(elapsed//60)}m{int(elapsed%60)}s | Est: {est_str} | Face: {len(to_keep)} | NoFace: {len(to_delete)}")

# Save results
result = {
    "total": total,
    "to_keep": [{"id": k["id"], "name": k["name"], "path": k["_path"]} for k in to_keep],
    "to_delete": [{"id": d["id"], "name": d["name"], "path": d["_path"], "size": d.get("size", 0)} for d in to_delete],
    "errors": errors,
    "to_keep_count": len(to_keep),
    "to_delete_count": len(to_delete),
}

with open("D:/Projects/ai-photo-template-miniapp/od_classify_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

size_delete = sum(d.get("size", 0) for d in to_delete)
print(f"\n=== Classification Complete ===")
print(f"Total: {total}")
print(f"Keep (has face): {len(to_keep)}")
print(f"Delete (no face): {len(to_delete)} ({size_delete / 1024 / 1024:.1f} MB)")
print(f"Errors: {len(errors)}")
print(f"Time: {int((time.time() - start_time) // 60)}m{int((time.time() - start_time) % 60)}s")
print(f"Result saved to od_classify_result.json")
