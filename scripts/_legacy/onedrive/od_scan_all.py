import json, requests, os, time

TOKEN_FILE = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"
with open(TOKEN_FILE) as f:
    token = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}
image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif', '.tiff'}

def paginate(url):
    items = []
    while url:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        if "error" in data:
            print(f"ERROR: {data['error'].get('message', '')}")
            break
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return items

# Step 1: Get all top-level items
print("Scanning OneDrive root...")
root_items = paginate("https://graph.microsoft.com/v1.0/me/drive/root/children?$top=200&$select=id,name,size,file,folder")
print(f"Root items: {len(root_items)}")

# Find folders
folders = [i for i in root_items if "folder" in i]
print(f"Folders: {len(folders)}")

# Step 2: Recursively scan all folders for images
all_images = []
scanned = 0

def scan_folder(folder_id, folder_name, path=""):
    global all_images, scanned
    current_path = f"{path}/{folder_name}" if path else folder_name
    items = paginate(f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children?$top=200&$select=id,name,size,file,folder")
    
    for item in items:
        if "folder" in item:
            scan_folder(item["id"], item["name"], current_path)
        elif "file" in item:
            ext = os.path.splitext(item["name"])[1].lower()
            if ext in image_exts:
                item["_path"] = current_path
                all_images.append(item)
                scanned += 1
                if scanned % 50 == 0:
                    print(f"  Found {scanned} images so far...")

for folder in folders:
    print(f"Scanning [{folder['name']}]...")
    scan_folder(folder["id"], folder["name"])

# Step 3: Also check root for image files
for item in root_items:
    if "file" in item:
        ext = os.path.splitext(item["name"])[1].lower()
        if ext in image_exts:
            item["_path"] = ""
            all_images.append(item)

print(f"\n=== Found {len(all_images)} images ===")
total_size = sum(img.get("size", 0) for img in all_images)
print(f"Total size: {total_size / 1024 / 1024:.1f} MB")

with open("D:/Projects/ai-photo-template-miniapp/onedrive_images.json", "w", encoding="utf-8") as f:
    json.dump(all_images, f, ensure_ascii=False, indent=2)

# Also save a summary
with open("D:/Projects/ai-photo-template-miniapp/od_scan_report.txt", "w", encoding="utf-8") as f:
    f.write(f"Total images: {len(all_images)}\n")
    f.write(f"Total size: {total_size / 1024 / 1024:.1f} MB\n\n")
    for img in all_images:
        f.write(f"[{img['_path']}] {img['name']} ({img.get('size',0)/1024:.0f}KB)\n")

print("Done!")
