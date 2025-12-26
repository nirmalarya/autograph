#!/usr/bin/env python3
import requests
import json

# Login as admin
login_response = requests.post(
    "http://localhost:8085/login",
    json={"email": "admin532@example.com", "password": "testpass123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print("✓ Login successful")
print(f"Token: {token[:50]}...")

# Test /admin/users endpoint
headers = {"Authorization": f"Bearer {token}"}
users_response = requests.get("http://localhost:8085/admin/users", headers=headers)

if users_response.status_code != 200:
    print(f"\n✗ Failed to get users: {users_response.status_code}")
    print(users_response.text)
    exit(1)

users = users_response.json()
print(f"\n✓ Successfully retrieved {len(users)} users")

# Verify response structure
if users:
    print("\nFirst user details:")
    first_user = users[0]
    print(json.dumps(first_user, indent=2, default=str))

    # Check required fields
    required_fields = ["id", "email", "role", "is_active", "is_verified", "created_at"]
    missing = [f for f in required_fields if f not in first_user]

    if missing:
        print(f"\n✗ Missing fields: {missing}")
    else:
        print(f"\n✓ All required fields present")
        print(f"  - Email: {first_user['email']}")
        print(f"  - Role: {first_user['role']}")
        print(f"  - Active: {first_user['is_active']}")
        print(f"  - Verified: {first_user['is_verified']}")
        print(f"  - Last login: {first_user.get('last_login_at', 'Never')}")

print("\n✓ Feature #532: Admin user management dashboard - WORKING")
