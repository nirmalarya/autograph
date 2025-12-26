#!/usr/bin/env python3
import requests
import bcrypt

# First, create a regular non-admin user
password_hash = bcrypt.hashpw(b'testpass123', bcrypt.gensalt()).decode()

# Insert non-admin user via database
import subprocess
result = subprocess.run([
    'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-c',
    f"INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at) VALUES ('user-532-test', 'user532@example.com', '{password_hash}', 'Regular User', 'user', true, true, NOW(), NOW()) ON CONFLICT (email) DO UPDATE SET role = 'user';"
], capture_output=True)

print("Created regular user")

# Login as regular user
login_response = requests.post(
    "http://localhost:8085/login",
    json={"email": "user532@example.com", "password": "testpass123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
print("✓ Login as regular user successful")

# Try to access /admin/users endpoint
headers = {"Authorization": f"Bearer {token}"}
users_response = requests.get("http://localhost:8085/admin/users", headers=headers)

print(f"\nAttempting to access /admin/users as regular user:")
print(f"Status code: {users_response.status_code}")

if users_response.status_code == 403:
    print("✓ Access denied (403 Forbidden) - Correct!")
    print(f"Response: {users_response.json()}")
elif users_response.status_code == 401:
    print("✓ Access denied (401 Unauthorized) - Correct!")
    print(f"Response: {users_response.json()}")
else:
    print(f"✗ SECURITY ISSUE: Regular user got status {users_response.status_code}")
    print(f"Response: {users_response.text}")
    exit(1)

print("\n✓ Feature #532: Access control verified - non-admins cannot access")
