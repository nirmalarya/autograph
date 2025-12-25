#!/usr/bin/env python3
"""Debug OAuth refresh token issue."""
import requests
import json
import time
import jwt
from urllib.parse import urlparse, parse_qs
import psycopg2

AUTH_BASE = "http://localhost:8080/api/auth"
TEST_EMAIL = f"oauth_debug_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!@#"
OAUTH_APP_NAME = "Debug OAuth App"
OAUTH_REDIRECT_URI = "http://localhost:3000/oauth/callback"
SECRET_KEY = 'dev-secret-key-change-in-production-use-openssl-rand-hex-32'

# Register and verify user
resp = requests.post(f"{AUTH_BASE}/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
user_id = resp.json()["id"]
print(f"✅ User registered: {TEST_EMAIL}")

conn = psycopg2.connect(host="localhost", port=5432, database="autograph", user="autograph", password="autograph_dev_password")
cur = conn.cursor()
cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (TEST_EMAIL,))
conn.commit()
cur.close()
conn.close()
print(f"✅ User verified")

# Login
resp = requests.post(f"{AUTH_BASE}/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
access_token = resp.json()["access_token"]
print(f"✅ Logged in")

# Create OAuth app
resp = requests.post(
    f"{AUTH_BASE}/oauth/apps",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "name": OAUTH_APP_NAME,
        "description": "Debug test",
        "redirect_uris": [OAUTH_REDIRECT_URI],
        "allowed_scopes": ["read", "write"]
    }
)
oauth_app = resp.json()
client_id = oauth_app["client_id"]
client_secret = oauth_app["client_secret"]
print(f"✅ OAuth app created: {client_id}")

# Request authorization
resp = requests.get(
    f"{AUTH_BASE}/oauth/authorize",
    headers={"Authorization": f"Bearer {access_token}"},
    params={
        "client_id": client_id,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "read,write",
        "state": "test123"
    },
    allow_redirects=False
)
redirect_location = resp.headers.get("Location")
parsed_url = urlparse(redirect_location)
query_params = parse_qs(parsed_url.query)
auth_code = query_params.get("code", [None])[0]
print(f"✅ Authorization code: {auth_code[:20]}...")

# Exchange code for tokens
resp = requests.post(
    f"{AUTH_BASE}/oauth/token",
    json={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret
    }
)
token_data = resp.json()
oauth_access_token = token_data["access_token"]
oauth_refresh_token = token_data["refresh_token"]
print(f"✅ Access token received")
print(f"✅ Refresh token received")

# Decode refresh token to see what's in it
decoded = jwt.decode(oauth_refresh_token, SECRET_KEY, algorithms=['HS256'], options={"verify_signature": True})
print(f"\n🔍 Refresh token contents:")
print(f"   type: {decoded.get('type')}")
print(f"   jti: {decoded.get('jti')}")
print(f"   sub: {decoded.get('sub')}")
print(f"   client_id: {decoded.get('client_id')}")
print()

# Try to refresh
print(f"Attempting refresh...")
resp = requests.post(
    f"{AUTH_BASE}/oauth/token",
    json={
        "grant_type": "refresh_token",
        "refresh_token": oauth_refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
)

if resp.status_code == 200:
    print(f"✅ Token refresh SUCCESSFUL!")
    new_token = resp.json()
    print(f"   New access token: {new_token['access_token'][:50]}...")
else:
    print(f"❌ Token refresh FAILED: {resp.status_code}")
    print(f"   Error: {resp.text}")
