#!/usr/bin/env python3
"""
Feature #90 Validation: Remember Me Functionality
Tests that remember_me extends session to 30 days
"""

import requests
import time
import jwt
from datetime import datetime, timezone

# Base URLs
AUTH_URL = "https://localhost:8085"
API_URL = "https://localhost:8080"

# Disable SSL warnings for local testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def decode_token(token):
    """Decode JWT token without verification to inspect claims."""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def register_and_verify_user(email, password):
    """Register and verify a user."""
    register_data = {
        "email": email,
        "password": password,
        "name": "Test User"
    }

    print(f"Registering user: {email}")
    response = requests.post(f"{AUTH_URL}/register", json=register_data, verify=False)
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    print("✅ User registered successfully")

    # Get verification token from Docker logs
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '50', 'autograph-auth-service'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Look for the most recent verification token
        verification_token = None
        for line in reversed(result.stdout.split('\n')):
            if 'Verification token created:' in line:
                verification_token = line.split('Verification token created:')[1].strip()
                break

        if not verification_token:
            print("❌ Could not extract verification token from logs")
            return False

        print(f"✅ Extracted verification token")

        # Verify email
        verify_response = requests.post(f"{AUTH_URL}/email/verify", json={
            "token": verification_token
        }, verify=False)

        if verify_response.status_code != 200:
            print(f"❌ Email verification failed: {verify_response.status_code}")
            return False

        print("✅ Email verified successfully")
        return True

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def test_remember_me_functionality():
    """Test remember me functionality extends session to 30 days."""
    print("\n" + "="*60)
    print("Testing Feature #90: Remember Me Functionality")
    print("="*60)

    # Test 1: Login WITH remember_me=true
    print("\n1. Testing login WITH remember_me=true...")
    print("-" * 40)

    # Register and verify a test user
    email = f"rememberme_test_{int(time.time())}@example.com"
    password = "SecurePass123!"

    if not register_and_verify_user(email, password):
        return False

    # Login with remember_me=true
    login_data = {
        "email": email,
        "password": password,
        "remember_me": True
    }

    print("\nLogging in with remember_me=true...")
    response = requests.post(f"{AUTH_URL}/login", json=login_data, verify=False)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False

    tokens_remember = response.json()
    print("✅ Login successful")

    # Decode and check refresh token expiry
    refresh_claims = decode_token(tokens_remember["refresh_token"])
    if not refresh_claims:
        print("❌ Failed to decode refresh token")
        return False

    exp_timestamp = refresh_claims.get("exp")
    iat_timestamp = refresh_claims.get("iat")

    if not exp_timestamp or not iat_timestamp:
        print("❌ Missing exp or iat claims in refresh token")
        return False

    # Calculate TTL in days
    ttl_seconds = exp_timestamp - iat_timestamp
    ttl_days = ttl_seconds / (24 * 60 * 60)

    print(f"\nRefresh token details (remember_me=true):")
    print(f"  Issued at:  {datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)}")
    print(f"  Expires at: {datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)}")
    print(f"  TTL: {ttl_days:.1f} days ({ttl_seconds} seconds)")

    if ttl_days < 29.5 or ttl_days > 30.5:
        print(f"❌ Expected 30 days TTL, got {ttl_days:.1f} days")
        return False

    print("✅ Refresh token TTL is 30 days")

    # Test 2: Login WITHOUT remember_me (or remember_me=false)
    print("\n2. Testing login WITHOUT remember_me...")
    print("-" * 40)

    # Register and verify another test user
    email2 = f"no_remember_{int(time.time())}@example.com"
    password2 = "SecurePass456!"

    if not register_and_verify_user(email2, password2):
        return False

    # Login without remember_me
    login_data2 = {
        "email": email2,
        "password": password2,
        "remember_me": False
    }

    print("\nLogging in with remember_me=false...")
    response = requests.post(f"{AUTH_URL}/login", json=login_data2, verify=False)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False

    tokens_no_remember = response.json()
    print("✅ Login successful")

    # Decode and check refresh token expiry
    refresh_claims2 = decode_token(tokens_no_remember["refresh_token"])
    if not refresh_claims2:
        print("❌ Failed to decode refresh token")
        return False

    exp_timestamp2 = refresh_claims2.get("exp")
    iat_timestamp2 = refresh_claims2.get("iat")

    if not exp_timestamp2 or not iat_timestamp2:
        print("❌ Missing exp or iat claims in refresh token")
        return False

    # Calculate TTL in days
    ttl_seconds2 = exp_timestamp2 - iat_timestamp2
    ttl_days2 = ttl_seconds2 / (24 * 60 * 60)

    print(f"\nRefresh token details (remember_me=false):")
    print(f"  Issued at:  {datetime.fromtimestamp(iat_timestamp2, tz=timezone.utc)}")
    print(f"  Expires at: {datetime.fromtimestamp(exp_timestamp2, tz=timezone.utc)}")
    print(f"  TTL: {ttl_days2:.1f} days ({ttl_seconds2} seconds)")

    # Without remember_me, session should be shorter (browser session)
    # Typically 1 day or less
    if ttl_days2 > 2:
        print(f"❌ Expected shorter TTL (≤1 day), got {ttl_days2:.1f} days")
        print("   Without remember_me, session should expire sooner")
        return False

    print("✅ Refresh token TTL is shorter without remember_me")

    # Test 3: Verify both tokens work
    print("\n3. Verifying both tokens work...")
    print("-" * 40)

    # Test /me endpoint with remember_me token
    headers1 = {"Authorization": f"Bearer {tokens_remember['access_token']}"}
    response1 = requests.get(f"{AUTH_URL}/me", headers=headers1, verify=False)
    if response1.status_code != 200:
        print(f"❌ /me endpoint failed with remember_me token: {response1.status_code}")
        return False
    print("✅ Remember_me token works for /me endpoint")

    # Test /me endpoint with non-remember token
    headers2 = {"Authorization": f"Bearer {tokens_no_remember['access_token']}"}
    response2 = requests.get(f"{AUTH_URL}/me", headers=headers2, verify=False)
    if response2.status_code != 200:
        print(f"❌ /me endpoint failed with non-remember token: {response2.status_code}")
        return False
    print("✅ Non-remember token works for /me endpoint")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Feature #90 working correctly")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = test_remember_me_functionality()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
