#!/usr/bin/env python3
import requests
import jwt as pyjwt
import subprocess

# Login with the test user
r = requests.post('http://localhost:8080/api/auth/login', json={
    'email': 'oauth_scope_test_1766668901@example.com',
    'password': 'SecurePassword123!@#'
})
if r.status_code != 200:
    print(f'Login failed: {r.status_code}')
    exit(1)

jwt_token = r.json()['access_token']
print('✓ Logged in')

# Get OAuth app
r = requests.get('http://localhost:8080/api/auth/oauth/apps', headers={'Authorization': f'Bearer {jwt_token}'})
if r.status_code != 200 or not r.json():
    print(f'No OAuth apps: {r.status_code}')
    exit(1)

app = r.json()[0]
print(f'✓ OAuth app: {app["client_id"]}')

# Get latest OAuth access token from the test
result = subprocess.run([
    'docker', 'exec', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-t', '-A',
    '-c', f"SELECT token_jti FROM oauth_access_tokens WHERE app_id = '{app['id']}' ORDER BY created_at DESC LIMIT 1;"
], capture_output=True, text=True)

if not result.stdout.strip():
    print('No OAuth tokens found in database')
    exit(1)

token_jti = result.stdout.strip()
print(f'✓ Found OAuth token JTI: {token_jti}')

# The actual OAuth token from the last test should be in the response
# Let me get it from the test by running a quick auth flow
import secrets
import uuid
from datetime import datetime, timedelta
import json

# Create new auth code
code = secrets.token_urlsafe(32)
code_id = str(uuid.uuid4())
expires_at = datetime.utcnow() + timedelta(minutes=10)

# Decode JWT to get user_id
payload = pyjwt.decode(jwt_token, options={'verify_signature': False})
user_id = payload['sub']

# Insert auth code with 'read' scope
scopes_json = json.dumps(['read']).replace("'", "''")
subprocess.run([
    'docker', 'exec', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph',
    '-c', (
        f"INSERT INTO oauth_authorization_codes "
        f"(id, app_id, user_id, code, redirect_uri, scopes, expires_at, is_used, created_at) "
        f"VALUES ('{code_id}', '{app['id']}', '{user_id}', '{code}', 'http://localhost:3000/callback', "
        f"'{scopes_json}', '{expires_at.isoformat()}', FALSE, '{datetime.utcnow().isoformat()}');"
    )
], capture_output=True)

# Exchange for OAuth token
r = requests.post('http://localhost:8080/api/auth/oauth/token', json={
    'grant_type': 'authorization_code',
    'client_id': app['client_id'],
    'client_secret': app['client_secret'],
    'code': code,
    'redirect_uri': 'http://localhost:3000/callback'
})

if r.status_code != 200:
    print(f'Token exchange failed: {r.status_code} - {r.text}')
    exit(1)

oauth_token = r.json()['access_token']
print(f'✓ Got OAuth access token')

# Decode and inspect
oauth_payload = pyjwt.decode(oauth_token, options={'verify_signature': False})
print('\n' + '='*60)
print('OAuth JWT Token Payload:')
print('='*60)
for key, value in oauth_payload.items():
    print(f'{key}: {value}')
print('='*60)

# Check the type field
token_type = oauth_payload.get('type')
print(f'\nToken type: "{token_type}"')
print(f'Expected: "oauth_access"')
print(f'Match: {token_type == "oauth_access"}')
