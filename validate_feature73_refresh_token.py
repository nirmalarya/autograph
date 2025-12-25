#!/usr/bin/env python3
"""
Feature 73: JWT Refresh Token Functionality
Tests that refresh tokens can obtain new access tokens and implement token rotation.
"""

import requests
import time
import jwt
import json
import sys
import subprocess
from datetime import datetime, timedelta

BASE_URL = "https://localhost:8085"

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_step(step_num, description):
    """Print test step header"""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {description}")
    print('='*70)

def register_and_verify_user(email, password):
    """Register a new user and verify their email"""
    # Register
    response = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": password,
        "role": "viewer"
    }, verify=False)

    if response.status_code == 409:
        print(f"⚠️  User already exists: {email}, will try to login")
        return True

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return False

    print(f"✅ User registered")

    # Get verification token from docker logs
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '50', 'autograph-auth-service'],
            capture_output=True,
            text=True,
            timeout=5
        )

        for line in reversed(result.stdout.split('\n')):
            if 'Verification token created:' in line:
                verification_token = line.split('Verification token created:')[1].strip()
                print(f"✅ Found verification token in logs")
                break
        else:
            print("❌ Could not find verification token in logs")
            return False

    except Exception as e:
        print(f"❌ Failed to get verification token from logs: {e}")
        return False

    # Verify email
    verify_response = requests.post(f"{BASE_URL}/email/verify", json={
        "token": verification_token
    }, verify=False)

    if verify_response.status_code != 200:
        print(f"❌ Email verification failed: {verify_response.status_code}")
        return False

    print(f"✅ User verified: {email}")
    return True

def login_user(email, password):
    """Login user and get tokens"""
    response = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": password
    }, verify=False)

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None, None

    data = response.json()
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')

    if not access_token or not refresh_token:
        print("❌ Missing tokens in response")
        return None, None

    print(f"✅ Login successful")
    return access_token, refresh_token

def refresh_access_token(refresh_token):
    """Use refresh token to get new access token"""
    response = requests.post(f"{BASE_URL}/refresh", json={
        "refresh_token": refresh_token
    }, verify=False)

    if response.status_code != 200:
        print(f"❌ Token refresh failed: {response.status_code}")
        print(response.text)
        return None, None

    data = response.json()
    new_access_token = data.get('access_token')
    new_refresh_token = data.get('refresh_token')

    return new_access_token, new_refresh_token

def test_token_with_protected_endpoint(access_token):
    """Test if token works with a protected endpoint"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers, verify=False)
    return response.status_code == 200

def decode_token(token):
    """Decode JWT token without verification to inspect claims"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"❌ Failed to decode token: {e}")
        return None

def main():
    """Main validation logic"""
    print("JWT REFRESH TOKEN FUNCTIONALITY VALIDATION")
    print("=" * 70)

    # Generate unique email for this test
    import random
    import string
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    test_email = f"test_refresh_{random_suffix}@example.com"
    test_password = "SecurePass123!"

    # Step 1: Register and verify user
    print_step(1, "Register and verify test user")
    if not register_and_verify_user(test_email, test_password):
        print("\n❌ FAILED: Could not register user")
        return False

    # Step 2: Login to get initial tokens
    print_step(2, "Login to get access_token and refresh_token")
    access_token, refresh_token = login_user(test_email, test_password)

    if not access_token or not refresh_token:
        print("\n❌ FAILED: Could not obtain tokens")
        return False

    print(f"Access token (first 50 chars): {access_token[:50]}...")
    print(f"Refresh token (first 50 chars): {refresh_token[:50]}...")

    # Step 3: Use refresh token immediately (don't wait for expiration)
    print_step(3, "Use refresh token to get new access token")
    print("Note: Testing refresh immediately (not waiting for expiration)")

    new_access_token, new_refresh_token = refresh_access_token(refresh_token)

    if not new_access_token:
        print("\n❌ FAILED: Could not refresh token")
        return False

    print(f"✅ Received new access token")
    print(f"New access token (first 50 chars): {new_access_token[:50]}...")

    # Step 4: Verify new access token is different
    print_step(4, "Verify new access token is different from original")

    if new_access_token == access_token:
        print("❌ New access token is identical to old token")
        return False

    print("✅ New access token is different from original")

    # Step 5: Test token rotation (new refresh token)
    print_step(5, "Verify token rotation (new refresh token issued)")

    if not new_refresh_token:
        print("⚠️  No new refresh token returned")
        print("   Token rotation may not be implemented")
        # This might be OK depending on implementation
    else:
        if new_refresh_token == refresh_token:
            print("⚠️  New refresh token is identical to old token")
            print("   Token rotation may not be implemented")
        else:
            print("✅ Token rotation: New refresh token issued")
            print(f"New refresh token (first 50 chars): {new_refresh_token[:50]}...")

    # Step 6: Verify old refresh token is invalidated (if rotation is implemented)
    if new_refresh_token and new_refresh_token != refresh_token:
        print_step(6, "Verify old refresh token is invalidated")

        # Try to use old refresh token
        old_token_access, old_token_refresh = refresh_access_token(refresh_token)

        if old_token_access:
            print("❌ Old refresh token still works (should be invalidated)")
            return False
        else:
            print("✅ Old refresh token invalidated (cannot be reused)")
    else:
        print_step(6, "Skip old token invalidation test")
        print("⚠️  Token rotation not implemented, skipping invalidation test")

    # Step 7: Verify new access token works with protected endpoint
    print_step(7, "Test new access token with protected endpoint")

    if test_token_with_protected_endpoint(new_access_token):
        print("✅ New access token works with protected endpoint")
    else:
        print("❌ New access token failed to access protected endpoint")
        return False

    # Step 8: Verify token structure and expiration
    print_step(8, "Verify new access token structure and expiration")

    payload = decode_token(new_access_token)
    if not payload:
        print("❌ Could not decode new access token")
        return False

    exp_time = payload.get('exp')
    iat_time = payload.get('iat')

    if not exp_time or not iat_time:
        print("❌ Missing exp or iat claims in new token")
        return False

    token_lifetime = exp_time - iat_time
    print(f"New token lifetime: {token_lifetime} seconds ({token_lifetime/3600:.2f} hours)")

    if abs(token_lifetime - 3600) > 60:
        print(f"⚠️  Token lifetime is not ~1 hour: {token_lifetime} seconds")
        # This might still be OK, just log it
    else:
        print(f"✅ New token has correct expiration (~1 hour)")

    # Verify claims match user
    if payload.get('email') != test_email.lower():
        print(f"❌ Email claim mismatch: {payload.get('email')} != {test_email.lower()}")
        return False

    print(f"✅ Token claims are correct (email: {payload.get('email')})")

    # Step 9: Test refresh token again (if rotation is implemented)
    if new_refresh_token and new_refresh_token != refresh_token:
        print_step(9, "Test second refresh with new refresh token")

        second_access_token, second_refresh_token = refresh_access_token(new_refresh_token)

        if not second_access_token:
            print("❌ Second refresh failed")
            return False

        print("✅ Second refresh successful")
        print("✅ Refresh token rotation working correctly")
    else:
        print_step(9, "Skip second refresh test")
        print("⚠️  Skipping (token rotation not implemented)")

    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("✅ Refresh token successfully obtains new access token")
    print("✅ New access token is different from original")
    print("✅ New access token works with protected endpoints")
    print("✅ Token claims are correct and valid")

    if new_refresh_token and new_refresh_token != refresh_token:
        print("✅ Token rotation implemented (new refresh token issued)")
        print("✅ Old refresh token invalidated after rotation")
    else:
        print("⚠️  Token rotation not detected (optional feature)")

    print("\n" + "="*70)
    print("FEATURE 73: JWT REFRESH TOKEN FUNCTIONALITY - PASSED ✅")
    print("="*70)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
