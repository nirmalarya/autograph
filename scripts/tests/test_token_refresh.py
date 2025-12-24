#!/usr/bin/env python3
"""
Test Suite for Features #73 and #75: Token Refresh with Rotation

Feature #73: JWT refresh token can be used to get new access token
Feature #75: Token refresh implements rotation (old refresh token invalidated)

This test suite verifies:
1. Refresh token can be exchanged for new tokens
2. New access token is valid and contains correct claims
3. New refresh token is returned (token rotation)
4. Old refresh token is invalidated after use
5. Attempting to reuse old refresh token fails
6. Token rotation prevents replay attacks
"""

import requests
import json
import time
from datetime import datetime
import jwt

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
FRONTEND_URL = "http://localhost:3000"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_step(step_num, description):
    """Print a test step."""
    print(f"\nStep {step_num}: {description}")

def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")

def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")

def test_feature_73_token_refresh():
    """Test Feature #73: JWT refresh token can be used to get new access token."""
    print_header("FEATURE #73 TEST SUITE: Token Refresh")
    print(f"Testing against:")
    print(f"  - Backend: {AUTH_SERVICE_URL}")
    print(f"  - Frontend: {FRONTEND_URL}")
    print(f"  - Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Token refresh returns new tokens
    print_header("TEST 1: Token Refresh Returns New Tokens")
    
    # Step 1: Register and login to get initial tokens
    print_step(1, "Registering and logging in to get initial tokens")
    test_email = f"test_refresh_{int(time.time())}@example.com"
    test_password = "SecurePass123!"
    
    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Test Refresh User"
        }
    )
    
    if register_response.status_code != 201:
        print_error(f"Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    print_success(f"User registered: {test_email}")
    
    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    
    if login_response.status_code != 200:
        print_error(f"Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    initial_access_token = login_data.get("access_token")
    initial_refresh_token = login_data.get("refresh_token")
    
    print_success(f"Login successful")
    print(f"  - Initial access token: {initial_access_token[:50]}...")
    print(f"  - Initial refresh token: {initial_refresh_token[:50]}...")
    
    # Step 2: Use refresh token to get new tokens
    print_step(2, "Using refresh token to get new tokens")
    
    refresh_response = requests.post(
        f"{AUTH_SERVICE_URL}/refresh",
        json={
            "refresh_token": initial_refresh_token
        }
    )
    
    if refresh_response.status_code != 200:
        print_error(f"Token refresh failed: {refresh_response.status_code}")
        print(f"Response: {refresh_response.text}")
        return False
    
    refresh_data = refresh_response.json()
    new_access_token = refresh_data.get("access_token")
    new_refresh_token = refresh_data.get("refresh_token")
    
    print_success("Token refresh successful")
    print(f"  - New access token: {new_access_token[:50]}...")
    print(f"  - New refresh token: {new_refresh_token[:50]}...")
    
    # Step 3: Verify new access token is valid
    print_step(3, "Verifying new access token is valid")
    
    # Decode without verification to check structure
    new_access_payload = jwt.decode(new_access_token, options={"verify_signature": False})
    
    required_claims = ['sub', 'email', 'role', 'exp', 'iat', 'type']
    missing_claims = [claim for claim in required_claims if claim not in new_access_payload]
    
    if missing_claims:
        print_error(f"New access token missing claims: {missing_claims}")
        return False
    
    print_success("New access token contains all required claims:")
    print(f"  - Subject: {new_access_payload.get('sub')}")
    print(f"  - Email: {new_access_payload.get('email')}")
    print(f"  - Role: {new_access_payload.get('role')}")
    print(f"  - Type: {new_access_payload.get('type')}")
    
    # Step 4: Verify new refresh token is different
    print_step(4, "Verifying new refresh token is different (token rotation)")
    
    if new_refresh_token == initial_refresh_token:
        print_error("New refresh token is the same as old token (rotation not working)")
        return False
    
    print_success("New refresh token is different from old token (rotation working)")
    
    # Decode new refresh token
    new_refresh_payload = jwt.decode(new_refresh_token, options={"verify_signature": False})
    print(f"  - New refresh token JTI: {new_refresh_payload.get('jti')}")
    
    # Step 5: Use new access token to access protected endpoint
    print_step(5, "Using new access token to access protected endpoint")
    
    me_response = requests.get(
        f"{AUTH_SERVICE_URL}/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    if me_response.status_code != 200:
        print_error(f"Protected endpoint access failed: {me_response.status_code}")
        print(f"Response: {me_response.text}")
        return False
    
    user_data = me_response.json()
    print_success("Protected endpoint access successful")
    print(f"  - User ID: {user_data.get('id')}")
    print(f"  - Email: {user_data.get('email')}")
    
    print_header("✅ TEST 1 PASSED: Token refresh returns new tokens")
    
    return {
        "initial_refresh_token": initial_refresh_token,
        "new_refresh_token": new_refresh_token,
        "new_access_token": new_access_token
    }


def test_feature_75_token_rotation(tokens):
    """Test Feature #75: Token refresh implements rotation (old refresh token invalidated)."""
    print_header("FEATURE #75 TEST SUITE: Token Rotation")
    
    initial_refresh_token = tokens["initial_refresh_token"]
    new_refresh_token = tokens["new_refresh_token"]
    
    # Test 2: Old refresh token is invalidated
    print_header("TEST 2: Old Refresh Token is Invalidated")
    
    # Step 1: Attempt to use old refresh token again
    print_step(1, "Attempting to use old refresh token (should fail)")
    
    reuse_response = requests.post(
        f"{AUTH_SERVICE_URL}/refresh",
        json={
            "refresh_token": initial_refresh_token
        }
    )
    
    if reuse_response.status_code == 200:
        print_error("Old refresh token was accepted (rotation not working)")
        return False
    
    if reuse_response.status_code != 401:
        print_error(f"Unexpected status code: {reuse_response.status_code} (expected 401)")
        print(f"Response: {reuse_response.text}")
        return False
    
    error_data = reuse_response.json()
    error_detail = error_data.get("detail", "")
    
    print_success(f"Old refresh token rejected with 401 Unauthorized")
    print(f"  - Error message: {error_detail}")
    
    # Step 2: Verify error message indicates token was already used
    print_step(2, "Verifying error message indicates token was already used")
    
    if "already used" not in error_detail.lower():
        print_error(f"Error message doesn't indicate token reuse: {error_detail}")
        return False
    
    print_success("Error message correctly indicates token was already used")
    
    # Step 3: Use new refresh token successfully
    print_step(3, "Using new refresh token (should succeed)")
    
    new_refresh_response = requests.post(
        f"{AUTH_SERVICE_URL}/refresh",
        json={
            "refresh_token": new_refresh_token
        }
    )
    
    if new_refresh_response.status_code != 200:
        print_error(f"New refresh token failed: {new_refresh_response.status_code}")
        print(f"Response: {new_refresh_response.text}")
        return False
    
    print_success("New refresh token works correctly")
    
    # Get the latest tokens
    latest_tokens = new_refresh_response.json()
    latest_refresh_token = latest_tokens.get("refresh_token")
    
    # Step 4: Verify token rotation prevents replay attacks
    print_step(4, "Verifying token rotation prevents replay attacks")
    
    # Try to use the new refresh token again (it should now be invalidated)
    replay_response = requests.post(
        f"{AUTH_SERVICE_URL}/refresh",
        json={
            "refresh_token": new_refresh_token
        }
    )
    
    if replay_response.status_code == 200:
        print_error("Token reuse was allowed (replay attack possible)")
        return False
    
    print_success("Token rotation prevents replay attacks")
    print(f"  - Reused token rejected with status: {replay_response.status_code}")
    
    print_header("✅ TEST 2 PASSED: Token rotation prevents replay attacks")
    
    return True


def test_feature_73_complete():
    """Complete test for Feature #73."""
    print_header("TESTING FEATURE #73: JWT Refresh Token Can Be Used to Get New Access Token")
    
    tokens = test_feature_73_token_refresh()
    
    if not tokens:
        print_header("❌ FEATURE #73 TEST FAILED")
        return False
    
    print_header("✅ FEATURE #73 TEST PASSED")
    return tokens


def test_feature_75_complete(tokens):
    """Complete test for Feature #75."""
    print_header("TESTING FEATURE #75: Token Refresh Implements Rotation")
    
    result = test_feature_75_token_rotation(tokens)
    
    if not result:
        print_header("❌ FEATURE #75 TEST FAILED")
        return False
    
    print_header("✅ FEATURE #75 TEST PASSED")
    return True


def main():
    """Run all tests."""
    print_header("TOKEN REFRESH TEST SUITE")
    print("Testing Features #73 and #75")
    print()
    
    # Test Feature #73
    tokens = test_feature_73_complete()
    if not tokens:
        print_header("TEST SUITE FAILED")
        return 1
    
    # Test Feature #75
    result = test_feature_75_complete(tokens)
    if not result:
        print_header("TEST SUITE FAILED")
        return 1
    
    # Summary
    print_header("TEST SUMMARY")
    print("✅ PASS: Feature #73 - JWT refresh token can be used to get new access token")
    print("✅ PASS: Feature #75 - Token refresh implements rotation")
    print()
    print("Total: 2/2 tests passed (100.0%)")
    print()
    print("🎉 ALL TESTS PASSED! Features #73 and #75 are ready for production.")
    print()
    print("Features #73 and #75 Status: ✅ PASSING")
    
    return 0


if __name__ == "__main__":
    exit(main())
