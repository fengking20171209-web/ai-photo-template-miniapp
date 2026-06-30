import json, requests, os

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'onedrive_token.json')
with open(TOKEN_FILE) as f:
    token = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}

# Check drive quota
print("=== Drive Info ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
drive = resp.json()
quota = drive.get("quota", {})
print(f"Total: {quota.get('total', 0) / 1024**3:.1f} GB")
print(f"Used:  {quota.get('used', 0) / 1024**3:.1f} GB")
print(f"Remaining: {quota.get('remaining', 0) / 1024**3:.1f} GB")
print(f"State: {quota.get('state', 'unknown')}")
print(f"Drive type: {drive.get('driveType', 'unknown')}")

# Check special folders (Photos, Pictures, etc.)
print("\n=== Special Folders ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/special", headers=headers)
special = resp.json().get("value", [])
for s in special:
    print(f"  {s['name']} -> {s.get('id', 'N/A')}")

# Try the Photos API
print("\n=== Photos API ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/special/photos", headers=headers)
if resp.status_code == 200:
    photos_data = resp.json()
    children = photos_data.get("folder", {}).get("childCount", "N/A")
    print(f"Photos folder child count: {children}")
else:
    print(f"Photos API status: {resp.status_code}")
    print(resp.json())

# List ALL top-level items with more detail
print("\n=== All Root Items (detailed) ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/children?$top=200&$select=id,name,size,file,folder,createdDateTime", headers=headers)
items = resp.json().get("value", [])
for item in items:
    ftype = "FOLDER" if "folder" in item else "FILE"
    size_mb = item.get("size", 0) / 1024 / 1024
    print(f"  [{ftype}] {item['name']} ({size_mb:.2f} MB)")

# Search for all images across the entire drive
print("\n=== Search: all images ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/search(q='.jpg')?top=50&$select=id,name,size,parentReference", headers=headers)
search_data = resp.json()
found = search_data.get("value", [])
print(f"JPG search results: {len(found)}")
for img in found[:5]:
    print(f"  {img['name']} ({img.get('size',0)/1024:.0f}KB) in {img.get('parentReference',{}).get('path','')}")

resp2 = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/search(q='.png')?top=50&$select=id,name,size,parentReference", headers=headers)
found2 = resp2.json().get("value", [])
print(f"PNG search results: {len(found2)}")

resp3 = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/search(q='.heic')?top=50&$select=id,name,size,parentReference", headers=headers)
found3 = resp3.json().get("value", [])
print(f"HEIC search results: {len(found3)}")

resp4 = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/search(q='.jpeg')?top=50&$select=id,name,size,parentReference", headers=headers)
found4 = resp4.json().get("value", [])
print(f"JPEG search results: {len(found4)}")
