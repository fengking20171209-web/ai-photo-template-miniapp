import json, requests, time, sys

CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TENANT = "consumers"
SCOPE = "Files.ReadWrite.All offline_access User.Read"
TOKEN_PATH = "D:/Projects/ai-photo-template-miniapp/onedrive_token.json"

# Step 1: Get device code
resp = requests.post(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/devicecode", data={"client_id": CLIENT_ID, "scope": SCOPE})
dc = resp.json()
if "user_code" not in dc:
    print("ERROR:", dc)
    sys.exit(1)

print(f"CODE={dc['user_code']}")
print(f"URL=https://www.microsoft.com/link")
sys.stdout.flush()

# Step 2: Poll for token (up to 15 min)
device_code = dc["device_code"]
interval = dc.get("interval", 5)
start = time.time()

while time.time() - start < dc["expires_in"]:
    time.sleep(interval)
    resp = requests.post(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token", data={"client_id": CLIENT_ID, "grant_type": "urn:ietf:params:oauth:grant-type:device_code", "device_code": device_code})
    result = resp.json()
    
    if "access_token" in result:
        with open(TOKEN_PATH, "w") as f:
            json.dump(result, f)
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        me = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName", headers=headers).json()
        drive = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers).json()
        q = drive.get("quota", {})
        print(f"AUTH_OK")
        print(f"ACCOUNT={me.get('userPrincipalName', '?')}")
        print(f"NAME={me.get('displayName', '?')}")
        print(f"USED_GB={round(q.get('used', 0) / 1024**3, 2)}")
        print(f"TOTAL_GB={round(q.get('total', 0) / 1024**3, 1)}")
        sys.exit(0)
    
    err = result.get("error", "")
    if err == "authorization_pending":
        sys.stdout.write(".")
        sys.stdout.flush()
    elif err == "slow_down":
        interval += 5
    else:
        print(f"\nFAIL: {err} {result.get('error_description', '')[:200]}")
        sys.exit(1)

print("\nTIMEOUT")
sys.exit(1)
