import json, requests, os

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'onedrive_token.json')
with open(TOKEN_FILE) as f:
    token = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}
image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif', '.tiff', '.svg'}

def list_children(item_id=None, path="root"):
    if item_id:
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/children?$top=200&$select=id,name,size,file,folder"
    else:
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children?$top=200&$select=id,name,size,file,folder"
    
    all_items = []
    while url:
        resp = requests.get(url, headers=headers)
        data = resp.json()
        if "error" in data:
            print(f"ERROR at {path}: {data['error']}")
            return all_items
        all_items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return all_items

def scan(path="root", item_id=None, depth=0):
    items = list_children(item_id, path)
    images = []
    folders = []
    
    for item in items:
        name = item.get("name", "")
        if "folder" in item:
            folders.append(item)
        elif "file" in item:
            ext = os.path.splitext(name)[1].lower()
            if ext in image_exts:
                item["_path"] = path + "/" + name
                images.append(item)
    
    prefix = "  " * depth
    print(f"{prefix}[{path}] {len(folders)} folders, {len(images)} images")
    
    for folder in folders:
        child_images = scan(folder["name"], folder["id"], depth + 1)
        images.extend(child_images)
    
    return images

print("Scanning OneDrive for images...")
all_images = scan()
print(f"\n=== Total images found: {len(all_images)} ===")

# Show size summary
total_size = sum(img.get("size", 0) for img in all_images)
print(f"Total size: {total_size / 1024 / 1024:.1f} MB")

# Save image list for next step
with open("D:/Projects/ai-photo-template-miniapp/onedrive_images.json", "w", encoding="utf-8") as f:
    json.dump(all_images, f, ensure_ascii=False, indent=2)
print("Image list saved to onedrive_images.json")
