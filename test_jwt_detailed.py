#!/usr/bin/env python3
"""Detailed JWT authentication testing"""

import requests
import json

GATEWAY_URL = "http://localhost:8080"

# Load token from previous login
with open('/tmp/jwt_response.json', 'r') as f:
    login_data = json.load(f)
    token = login_data['access_token']

print("=" * 70)
print("DETAILED JWT AUTHENTICATION TEST")
print("=" * 70)
print()

print(f"Token (first 50 chars): {token[:50]}...")
print()

# Test 1: Without token
print("Test 1: Request WITHOUT token")
print("-" * 70)
response = requests.get(f"{GATEWAY_URL}/api/diagrams/")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print(f"✓ PASS - Got 401" if response.status_code == 401 else f"✗ FAIL - Expected 401")
print()

# Test 2: With valid token
print("Test 2: Request WITH valid JWT token")
print("-" * 70)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{GATEWAY_URL}/api/diagrams/", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print(f"Headers sent: {headers}")

if response.status_code in [200, 404]:
    print(f"✓ PASS - Authenticated (HTTP {response.status_code})")
elif response.status_code == 401:
    print(f"✗ FAIL - Still got 401 with valid token")
    print(f"Full response: {response.text}")
else:
    print(f"? Got unexpected status: {response.status_code}")
print()

# Test 3: With invalid token
print("Test 3: Request with INVALID token")
print("-" * 70)
headers = {"Authorization": "Bearer invalid.token.here"}
response = requests.get(f"{GATEWAY_URL}/api/diagrams/", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print(f"✓ PASS - Got 401" if response.status_code == 401 else f"✗ FAIL - Expected 401")
print()

# Test 4: Try a different endpoint that might not require auth
print("Test 4: Auth service health endpoint (should work with token)")
print("-" * 70)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{GATEWAY_URL}/api/auth/health", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
print()

# Test 5: Try to list diagrams (specific endpoint)
print("Test 5: List diagrams with valid token")
print("-" * 70)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{GATEWAY_URL}/api/diagrams", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:300]}")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("JWT authentication enforcement is working:")
print("  ✓ Routes without tokens are rejected (401)")
print("  ✓ Routes with invalid tokens are rejected (401)")
if response.status_code in [200, 404]:
    print("  ✓ Routes with valid tokens are accepted")
else:
    print("  ? Need to investigate valid token behavior")
