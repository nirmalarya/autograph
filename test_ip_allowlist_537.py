#!/usr/bin/env python3
"""Test IP allowlist feature (#537)."""

import requests
import json

BASE_URL = "http://localhost:8085"

def login_admin():
    """Login as admin and get token."""
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "admin-ip537@test.com",
            "password": "AdminPass123!"
        }
    )
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Login failed: {response.text}")
        return None

def configure_ip_allowlist(token):
    """Configure IP allowlist with test CIDR."""
    headers = {"Authorization": f"Bearer {token}"}

    # Configure allowlist: 192.168.1.0/24
    config = {
        "allowed_ips": ["192.168.1.0/24"],
        "enabled": True
    }

    response = requests.post(
        f"{BASE_URL}/admin/config/ip-allowlist",
        json=config,
        headers=headers
    )

    print(f"\n✅ Step 1: Configure allowlist")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_allowed_ip(token):
    """Test access from allowed IP (simulated via X-Forwarded-For)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": "192.168.1.5"
    }

    # Use /me endpoint instead of /health (health is excluded)
    response = requests.get(
        f"{BASE_URL}/me",
        headers=headers
    )

    print(f"\n✅ Step 2-3: Access from allowed IP (192.168.1.5)")
    print(f"Status: {response.status_code}")
    print(f"Expected: 200 (allowed)")
    return response.status_code == 200

def test_blocked_ip():
    """Test access from blocked IP (simulated via X-Forwarded-For)."""
    headers = {
        "X-Forwarded-For": "10.0.0.1"
    }

    # Try to access login endpoint (not health which is excluded)
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": "test@example.com",
            "password": "test"
        },
        headers=headers
    )

    print(f"\n✅ Step 4-5: Access from blocked IP (10.0.0.1)")
    print(f"Status: {response.status_code}")
    print(f"Expected: 403 (blocked)")
    print(f"Response: {response.text[:200]}")
    return response.status_code == 403

def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing Feature #537: IP Allowlist")
    print("=" * 70)

    # Login
    token = login_admin()
    if not token:
        print("❌ Failed to login")
        return False

    # Configure allowlist
    if not configure_ip_allowlist(token):
        print("❌ Failed to configure allowlist")
        return False

    # Test allowed IP
    if not test_allowed_ip(token):
        print("❌ Allowed IP was blocked (should be allowed)")
        return False

    # Test blocked IP
    if not test_blocked_ip():
        print("❌ Blocked IP was allowed (should be blocked)")
        return False

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Feature #537 working correctly!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
