#!/usr/bin/env python3
"""
Test suite for Features #76 and #77: Logout functionality

Feature #76: Logout invalidates current session
Feature #77: Logout all sessions invalidates all user tokens

This test suite verifies:
- Single session logout (Feature #76)
- All sessions logout (Feature #77)
- Token blacklisting in Redis
- Proper error handling
"""

import requests
import time
import jwt
from datetime import datetime

# Configuration
AUTH_URL = "http://localhost:8085"
FRONTEND_URL = "http://localhost:3000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")

def print_test(test_name):
    """Print a formatted test header."""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80 + "\n")

def print_step(step_num, description):
    """Print a formatted step."""
    print(f"\nStep {step_num}: {description}")

def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")

def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")

def register_and_login(email_suffix=""):
    """Helper function to register and login a user."""
    timestamp = int(time.time())
    test_email = f"test_logout_{timestamp}{email_suffix}@example.com"
    test_password = "TestPassword123!"
    
    # Register
    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test User"
    }
    
    register_response = requests.post(f"{AUTH_URL}/register", json=register_data)
    if register_response.status_code != 201:
        raise Exception(f"Registration failed: {register_response.text}")
    
    # Login
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    login_response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if login_response.status_code != 200:
        raise Exception(f"Login failed: {login_response.text}")
    
    tokens = login_response.json()
    return {
        "email": test_email,
        "password": test_password,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }

def test_logout_single_session():
    """Test Feature #76: Logout invalidates current session."""
    print_section("TESTING FEATURE #76: Logout Invalidates Current Session")
    
    print_section("FEATURE #76 TEST SUITE: Single Session Logout")
    print(f"Testing against:")
    print(f"  - Backend: {AUTH_URL}")
    print(f"  - Frontend: {FRONTEND_URL}")
    print(f"  - Timestamp: {datetime.now().isoformat()}")
    
    print_test("1: Logout Invalidates Current Session")
    
    try:
        # Step 1: Register and login
        print_step(1, "Registering and logging in to get access token")
        user = register_and_login()
        access_token = user["access_token"]
        print_success(f"User registered and logged in: {user['email']}")
        print_success(f"Access token: {access_token[:50]}...")
        
        # Step 2: Use token to access protected endpoint
        print_step(2, "Using token to access protected endpoint (/me)")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{AUTH_URL}/me", headers=headers)
        
        if me_response.status_code != 200:
            print_error(f"Failed to access protected endpoint: {me_response.status_code}")
            return False
        
        user_info = me_response.json()
        print_success("Protected endpoint access successful")
        print_success(f"User ID: {user_info['id']}")
        print_success(f"Email: {user_info['email']}")
        
        # Step 3: Logout
        print_step(3, "Sending POST /logout with access token")
        logout_response = requests.post(f"{AUTH_URL}/logout", headers=headers)
        
        if logout_response.status_code != 200:
            print_error(f"Logout failed: {logout_response.status_code} - {logout_response.text}")
            return False
        
        logout_data = logout_response.json()
        print_success("Logout successful")
        print_success(f"Response: {logout_data['message']}")
        
        # Step 4: Attempt to use same access token
        print_step(4, "Attempting to use same access token (should fail)")
        me_response_after = requests.get(f"{AUTH_URL}/me", headers=headers)
        
        if me_response_after.status_code == 401:
            print_success("Token correctly rejected with 401 Unauthorized")
            error_detail = me_response_after.json().get('detail', '')
            print_success(f"Error message: {error_detail}")
        else:
            print_error(f"Token was not rejected! Status: {me_response_after.status_code}")
            return False
        
        # Step 5: Verify token is in blacklist (implicit - already verified by step 4)
        print_step(5, "Verifying token added to blacklist")
        print_success("Token blacklist verified (token rejected on use)")
        
        # Step 6: Decode token to check expiry
        print_step(6, "Checking token expiry time")
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        exp = decoded.get('exp')
        iat = decoded.get('iat')
        
        if exp and iat:
            ttl = exp - iat
            print_success(f"Token TTL: {ttl} seconds ({ttl/60:.1f} minutes)")
            print_success("Blacklist entry will expire after token TTL")
        
        print_section("✅ TEST 1 PASSED: Logout invalidates current session")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logout_all_sessions():
    """Test Feature #77: Logout all sessions invalidates all user tokens."""
    print_section("TESTING FEATURE #77: Logout All Sessions")
    
    print_section("FEATURE #77 TEST SUITE: Logout All Sessions")
    
    print_test("2: Logout All Sessions Invalidates All Tokens")
    
    try:
        # Step 1: Login from "browser 1"
        print_step(1, "Login from browser 1 to get token_1")
        user1 = register_and_login()
        token_1 = user1["access_token"]
        print_success(f"User logged in: {user1['email']}")
        print_success(f"Token 1: {token_1[:50]}...")
        
        # Step 2: Login from "browser 2" (same user)
        print_step(2, "Login from browser 2 to get token_2 (same user)")
        login_data = {
            "email": user1["email"],
            "password": user1["password"]
        }
        login_response = requests.post(f"{AUTH_URL}/login", json=login_data)
        
        if login_response.status_code != 200:
            print_error(f"Second login failed: {login_response.status_code}")
            return False
        
        tokens = login_response.json()
        token_2 = tokens["access_token"]
        print_success(f"Second login successful")
        print_success(f"Token 2: {token_2[:50]}...")
        
        # Step 3: Verify both tokens work
        print_step(3, "Verifying both tokens work")
        headers_1 = {"Authorization": f"Bearer {token_1}"}
        headers_2 = {"Authorization": f"Bearer {token_2}"}
        
        me_response_1 = requests.get(f"{AUTH_URL}/me", headers=headers_1)
        me_response_2 = requests.get(f"{AUTH_URL}/me", headers=headers_2)
        
        if me_response_1.status_code != 200 or me_response_2.status_code != 200:
            print_error("One or both tokens don't work")
            return False
        
        print_success("Token 1 works ✓")
        print_success("Token 2 works ✓")
        
        # Step 4: Logout all sessions from browser 1
        print_step(4, "Sending POST /logout-all from browser 1")
        logout_all_response = requests.post(f"{AUTH_URL}/logout-all", headers=headers_1)
        
        if logout_all_response.status_code != 200:
            print_error(f"Logout all failed: {logout_all_response.status_code} - {logout_all_response.text}")
            return False
        
        logout_data = logout_all_response.json()
        print_success("Logout all successful")
        print_success(f"Response: {logout_data['message']}")
        
        # Step 5: Attempt to use token_1
        print_step(5, "Attempting to use token_1 (should fail)")
        me_response_1_after = requests.get(f"{AUTH_URL}/me", headers=headers_1)
        
        if me_response_1_after.status_code == 401:
            print_success("Token 1 correctly rejected with 401 Unauthorized")
            error_detail = me_response_1_after.json().get('detail', '')
            print_success(f"Error message: {error_detail}")
        else:
            print_error(f"Token 1 was not rejected! Status: {me_response_1_after.status_code}")
            return False
        
        # Step 6: Attempt to use token_2
        print_step(6, "Attempting to use token_2 (should also fail)")
        me_response_2_after = requests.get(f"{AUTH_URL}/me", headers=headers_2)
        
        if me_response_2_after.status_code == 401:
            print_success("Token 2 correctly rejected with 401 Unauthorized")
            error_detail = me_response_2_after.json().get('detail', '')
            print_success(f"Error message: {error_detail}")
        else:
            print_error(f"Token 2 was not rejected! Status: {me_response_2_after.status_code}")
            return False
        
        # Step 7: Verify all user sessions cleared
        print_step(7, "Verifying all user sessions cleared from Redis")
        print_success("All user sessions cleared (both tokens rejected)")
        
        print_section("✅ TEST 2 PASSED: Logout all sessions invalidates all tokens")
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all logout tests."""
    print_section("LOGOUT TEST SUITE")
    print("Testing Features #76 and #77")
    print()
    
    results = []
    
    # Test Feature #76
    result_76 = test_logout_single_session()
    results.append(("Feature #76", result_76))
    
    print_section("✅ FEATURE #76 TEST PASSED" if result_76 else "❌ FEATURE #76 TEST FAILED")
    
    # Test Feature #77
    result_77 = test_logout_all_sessions()
    results.append(("Feature #77", result_77))
    
    print_section("✅ FEATURE #77 TEST PASSED" if result_77 else "❌ FEATURE #77 TEST FAILED")
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for feature, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {feature}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print()
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
