#!/usr/bin/env python3
"""
Refresh Microsoft Teams OAuth token.
Uses device code flow to get a new token with refresh capability.
"""
import requests
import json
import time
import os

CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TOKEN_FILE = os.path.expanduser("~/.openclaw/workspace/microsoft-tokens.json")
SCOPES = "openid profile email https://graph.microsoft.com/Directory.ReadWrite.All https://graph.microsoft.com/Group.Read.All"

def get_device_code():
    """Get device code for auth"""
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/devicecode"
    data = {
        "client_id": CLIENT_ID,
        "scope": SCOPES
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()

def poll_for_token(device_code):
    """Poll for token using device code"""
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "device_code": device_code["device_code"],
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "scope": SCOPES
    }
    
    # Poll up to 120 seconds
    for _ in range(120):
        r = requests.post(url, data=data)
        result = r.json()
        
        if "access_token" in result:
            # Save token
            with open(TOKEN_FILE, "w") as f:
                json.dump(result, f, indent=2)
            print(f"SUCCESS: Token saved, expires in {result.get('expires_in', '?')}s")
            return result
        elif result.get("error") == "authorization_pending":
            time.sleep(device_code.get("interval", 5))
            continue
        else:
            print(f"ERROR: {result}")
            return None
    
    print("TIMEOUT: No token received")
    return None

def main():
    print("Getting device code...")
    device_code = get_device_code()
    print(f"User code: {device_code['user_code']}")
    print(f"URL: {device_code['verification_uri']}")
    print("Waiting for auth...")
    poll_for_token(device_code)

if __name__ == "__main__":
    main()
