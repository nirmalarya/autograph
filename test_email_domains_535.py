#!/usr/bin/env python3
import requests

# Login as admin
login_response = requests.post(
    "http://localhost:8085/login",
    json={"email": "admin532@example.com", "password": "testpass123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
print("✓ Admin login successful")

# Step 1: Configure allowed domains
print("\nStep 1: Configuring allowed domains to @bayer.com only...")
headers = {"Authorization": f"Bearer {token}"}
config_data = {
    "allowed_domains": ["@bayer.com"],
    "enabled": True
}

config_response = requests.post(
    "http://localhost:8085/admin/config/email-domains",
    headers=headers,
    json=config_data
)

if config_response.status_code != 200:
    print(f"✗ Failed to configure domains: {config_response.text}")
    exit(1)

print(f"✓ Email domains configured: {config_response.json()}")

# Step 2: Attempt to register with @gmail.com (should be blocked)
print("\nStep 2: Attempting to register with @gmail.com (should be blocked)...")
gmail_user = {
    "email": "testuser@gmail.com",
    "password": "TestPass123!",
    "full_name": "Gmail User"
}

gmail_response = requests.post(
    "http://localhost:8085/register",
    json=gmail_user
)

print(f"Response status: {gmail_response.status_code}")
if gmail_response.status_code == 403:
    print(f"✓ Registration blocked (403 Forbidden)")
    print(f"  Message: {gmail_response.json().get('detail')}")
else:
    print(f"✗ SECURITY ISSUE: Gmail user was not blocked! Status: {gmail_response.status_code}")
    print(f"  Response: {gmail_response.text}")
    exit(1)

# Step 3: Attempt to register with @bayer.com (should be allowed)
print("\nStep 3: Attempting to register with @bayer.com (should be allowed)...")
bayer_user = {
    "email": "employee@bayer.com",
    "password": "TestPass123!",
    "full_name": "Bayer Employee"
}

bayer_response = requests.post(
    "http://localhost:8085/register",
    json=bayer_user
)

print(f"Response status: {bayer_response.status_code}")
if bayer_response.status_code == 201:
    print(f"✓ Registration successful!")
    user_data = bayer_response.json()
    print(f"  User: {user_data.get('email')}")
    print(f"  ID: {user_data.get('id')}")
elif bayer_response.status_code == 409:
    print(f"✓ User already exists (expected if re-running test)")
else:
    print(f"✗ Registration failed: {bayer_response.status_code}")
    print(f"  Response: {bayer_response.text}")
    exit(1)

# Cleanup: Disable email domain restrictions
print("\nCleanup: Disabling email domain restrictions...")
cleanup_data = {
    "allowed_domains": [],
    "enabled": False
}
cleanup_response = requests.post(
    "http://localhost:8085/admin/config/email-domains",
    headers=headers,
    json=cleanup_data
)

if cleanup_response.status_code == 200:
    print("✓ Email domain restrictions disabled")

print("\n" + "="*70)
print("✅ Feature #535: Email domain restrictions - PASSING")
print("="*70)
print("\nVerification complete:")
print("✓ Configured allowed domains (@bayer.com)")
print("✓ Blocked signup from disallowed domain (@gmail.com)")
print("✓ Allowed signup from allowed domain (@bayer.com)")
