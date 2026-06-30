import json, requests, os

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'onedrive_token.json')
with open(TOKEN_FILE) as f:
    token = json.load(f)

headers = {"Authorization": f"Bearer {token['access_token']}"}

# Check Pictures folder
print("=== Pictures folder ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/special/pictures", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    print(f"Name: {data.get('name')}")
    print(f"Size: {data.get('size', 0)}")
    print(f"Child count: {data.get('folder', {}).get('childCount', 'N/A')}")
    
    # List children
    cid = data.get("id")
    if cid:
        resp2 = requests.get(f"https://graph.microsoft.com/v1.0/me/drive/items/{cid}/children?$top=20", headers=headers)
        children = resp2.json().get("value", [])
        print(f"Children: {len(children)}")
        for c in children:
            print(f"  {c['name']} ({c.get('size',0)/1024:.0f}KB)")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text[:300])

# Try camera roll
print("\n=== Camera Roll ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/special/cameraroll", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    print(f"Child count: {data.get('folder', {}).get('childCount', 'N/A')}")
else:
    print(f"Status: {resp.status_code}")

# Check Documents folder
print("\n=== Documents folder ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root:/Documents:/children?$top=20", headers=headers)
if resp.status_code == 200:
    items = resp.json().get("value", [])
    print(f"Items: {len(items)}")
    for item in items:
        ftype = "FOLDER" if "folder" in item else "FILE"
        print(f"  [{ftype}] {item['name']} ({item.get('size',0)/1024/1024:.1f}MB)")
else:
    print(f"Status: {resp.status_code}")

# Check who am I (to confirm account)
print("\n=== Account Info ===")
resp = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName", headers=headers)
me = resp.json()
print(f"Name: {me.get('displayName')}")
print(f"Email: {me.get('userPrincipalName')}")
