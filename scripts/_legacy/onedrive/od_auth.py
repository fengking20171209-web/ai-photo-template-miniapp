import json, requests, time, sys

CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TENANT = "consumers"
SCOPE = "Files.ReadWrite.All offline_access User.Read"

# Step 1: Request device code
print("Requesting device code...")
url = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/devicecode"
resp = requests.post(url, data={"client_id": CLIENT_ID, "scope": SCOPE})
dc = resp.json()

if "user_code" not in dc:
    print("ERROR:", dc)
    sys.exit(1)

print(f"\n========================================")
print(f"  Please open: https://www.microsoft.com/link")
print(f"  Enter code: {dc['user_code']}")
print(f"  Login with: aminu0918@outlook.com")
print(f"  Expires in: {dc['expires_in']} seconds")
print(f"========================================\n")

# Step 2: Poll for token
device_code = dc["device_code"]
interval = dc.get("interval", 5)
expires = dc["expires_in"]
start = time.time()

while time.time() - start < expires:
    time.sleep(interval)
    resp = requests.post(
        f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
        },
    )
    result = resp.json()
    
    if "access_token" in result:
        # Save token
        with open("D:/Projects/ai-photo-template-miniapp/onedrive_token.json", "w") as f:
            json.dump(result, f)
        
        # Get account info
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        me = requests.get("https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName", headers=headers).json()
        print(f"AUTH OK!")
        print(f"Account: {me.get('userPrincipalName', 'unknown')}")
        print(f"Name: {me.get('displayName', 'unknown')}")
        break
    
    err = result.get("error", "")
    if err == "authorization_pending":
        sys.stdout.write(".")
        sys.stdout.flush()
    elif err == "slow_down":
        interval += 5
    elif err == "authorization_declined":
        print("\nAuthorization declined!")
        sys.exit(1)
    elif err == "expired_token":
        print("\nDevice code expired!")
        sys.exit(1)
    else:
        print(f"\nError: {result}")
        sys.exit(1)
else:
    print("\nTimeout!")
    sys.exit(1)
