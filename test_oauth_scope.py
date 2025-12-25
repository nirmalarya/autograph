#!/usr/bin/env python3
import requests
import subprocess
import json
import secrets
from datetime import datetime, timedelta
import uuid

# Use existing test user
test_email = 'quick_test_1766668830@example.com'

# Get JWT (login)
r = requests.post('http://localhost:8080/api/auth/login', json={'email': test_email, 'password': 'Test123!@#'})
if r.status_code != 200:
    print(f'Login failed: {r.status_code}')
    exit(1)
jwt_token = r.json()['access_token']
print(f'✓ Logged in')

# Decode JWT to get user_id
import jwt as pyjwt
payload = pyjwt.decode(jwt_token, options={'verify_signature': False})
user_id = payload['sub']
print(f'✓ User ID: {user_id}')

# Get OAuth app
r = requests.get('http://localhost:8080/api/auth/oauth/apps', headers={'Authorization': f'Bearer {jwt_token}'})
if r.status_code != 200 or not r.json():
    print(f'No OAuth apps found')
    exit(1)
app = r.json()[0]
client_id = app['client_id']
client_secret = app['client_secret']
print(f'✓ OAuth app: {client_id}')

# Create authorization code with 'read' scope via DB
code = secrets.token_urlsafe(32)
code_id = str(uuid.uuid4())
expires_at = datetime.utcnow() + timedelta(minutes=10)

# Get app_id
result = subprocess.run([
    'docker', 'exec', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-t',
    '-c', f"SELECT id FROM oauth_apps WHERE client_id = '{client_id}';"
], capture_output=True, text=True)
app_id = result.stdout.strip()

# Insert auth code with 'read' scope
scopes_json = json.dumps(['read']).replace("'", "''")
subprocess.run([
    'docker', 'exec', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph',
    '-c', (
        f"INSERT INTO oauth_authorization_codes "
        f"(id, app_id, user_id, code, redirect_uri, scopes, expires_at, is_used, created_at) "
        f"VALUES ('{code_id}', '{app_id}', '{user_id}', '{code}', 'http://localhost:3000/callback', "
        f"'{scopes_json}', '{expires_at.isoformat()}', FALSE, '{datetime.utcnow().isoformat()}');"
    )
], capture_output=True)
print(f'✓ Auth code created with read scope')

# Exchange for OAuth token
r = requests.post('http://localhost:8080/api/auth/oauth/token', json={
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'redirect_uri': 'http://localhost:3000/callback'
})
if r.status_code != 200:
    print(f'Token exchange failed: {r.status_code} - {r.text}')
    exit(1)
oauth_token = r.json()['access_token']
scopes = r.json()['scope']
print(f'✓ OAuth token obtained with scopes: {scopes}')

# Decode OAuth token to verify
oauth_payload = pyjwt.decode(oauth_token, options={'verify_signature': False})
print(f'✓ Token type: {oauth_payload.get("type")}')
print(f'✓ Token scopes: {oauth_payload.get("scopes")}')

# Test GET (should work)
r = requests.get('http://localhost:8080/api/auth/me', headers={'Authorization': f'Bearer {oauth_token}'})
print(f'\nGET /api/auth/me: {r.status_code}' + (' ✓' if r.status_code == 200 else ' ✗'))

# Test POST (should fail with 403)
r = requests.post('http://localhost:8080/api/diagrams', headers={'Authorization': f'Bearer {oauth_token}'}, json={'title': 'Test', 'description': 'Test'})
print(f'POST /api/diagrams: {r.status_code}' + (' ✓ (403 - scope denied)' if r.status_code == 403 else f' ✗ (expected 403, got {r.status_code})'))
if r.status_code != 200:
    print(f'  Response: {r.text[:300]}')
