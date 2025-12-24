#!/usr/bin/env python3
"""
Test suite for Feature #68: User login with email and password returns JWT tokens

This test verifies:
1. User can log in with valid credentials
2. Login returns JWT access_token
3. Login returns JWT refresh_token
4. Access token expires in 1 hour
5. Refresh token expires in 30 days
6. Login page is accessible
"""

import requests
import time
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8085"
FRONTEND_URL = "http://localhost:3000"

def test_login_page_accessible():
    """Test 1: Verify login page is accessible"""
    print("\n" + "="*80)
    print("TEST 1: Login Page Accessible")
    print("="*80)
    
    try:
        response = requests.get(f"{FRONTEND_URL}/login", timeout=5)
        print(f"✓ Login page status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "Welcome Back" in response.text or "Sign in" in response.text or "Login" in response.text, \
            "Login page doesn't contain expected content"
        
        print("✓ Login page contains login form")
        print("\n✅ TEST 1 PASSED: Login page is accessible")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {str(e)}")
        return False


def test_user_login_returns_jwt_tokens():
    """Test 2: User login with valid credentials returns JWT tokens"""
    print("\n" + "="*80)
    print("TEST 2: User Login Returns JWT Tokens")
    print("="*80)
    
    try:
        # Step 1: Register a test user
        test_email = f"test_login_{int(time.time())}@example.com"
        test_password = "SecurePass123!"
        
        print(f"Step 1: Registering test user: {test_email}")
        register_response = requests.post(
            f"{BASE_URL}/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test Login User"
            },
            timeout=5
        )
        
        assert register_response.status_code == 201, \
            f"Registration failed with status {register_response.status_code}"
        print(f"✓ User registered successfully: {test_email}")
        
        # Step 2: Login with the registered user
        print(f"\nStep 2: Logging in with: {test_email}")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            },
            timeout=5
        )
        
        print(f"✓ Login response status: {login_response.status_code}")
        
        assert login_response.status_code == 200, \
            f"Expected 200 OK, got {login_response.status_code}"
        
        # Step 3: Verify response contains tokens
        login_data = login_response.json()
        print(f"✓ Login response received")
        
        assert "access_token" in login_data, "Response missing access_token"
        assert "refresh_token" in login_data, "Response missing refresh_token"
        
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        print(f"✓ Access token received (length: {len(access_token)})")
        print(f"✓ Refresh token received (length: {len(refresh_token)})")
        
        # Step 4: Verify tokens are valid JWTs
        print(f"\nStep 3: Verifying JWT token structure")
        
        # Decode without verification to check structure
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        
        print(f"✓ Access token is valid JWT")
        print(f"  - Subject: {access_payload.get('sub')}")
        print(f"  - Email: {access_payload.get('email')}")
        print(f"  - Role: {access_payload.get('role')}")
        print(f"  - Expires: {datetime.fromtimestamp(access_payload.get('exp'))}")
        
        print(f"✓ Refresh token is valid JWT")
        print(f"  - Subject: {refresh_payload.get('sub')}")
        print(f"  - Expires: {datetime.fromtimestamp(refresh_payload.get('exp'))}")
        
        # Step 5: Verify access token expiry (1 hour)
        print(f"\nStep 4: Verifying token expiry times")
        
        access_exp = datetime.fromtimestamp(access_payload['exp'])
        access_iat = datetime.fromtimestamp(access_payload['iat'])
        access_duration = (access_exp - access_iat).total_seconds()
        
        print(f"✓ Access token duration: {access_duration} seconds ({access_duration/3600} hours)")
        
        # Allow 1 minute tolerance
        assert 3540 <= access_duration <= 3660, \
            f"Access token should expire in 1 hour (3600s), got {access_duration}s"
        
        print(f"✓ Access token expires in ~1 hour (within tolerance)")
        
        # Step 6: Verify refresh token expiry (30 days)
        refresh_exp = datetime.fromtimestamp(refresh_payload['exp'])
        refresh_iat = datetime.fromtimestamp(refresh_payload['iat'])
        refresh_duration = (refresh_exp - refresh_iat).total_seconds()
        
        expected_30_days = 30 * 24 * 3600  # 2,592,000 seconds
        print(f"✓ Refresh token duration: {refresh_duration} seconds ({refresh_duration/(24*3600)} days)")
        
        # Allow 1 hour tolerance
        assert expected_30_days - 3600 <= refresh_duration <= expected_30_days + 3600, \
            f"Refresh token should expire in 30 days ({expected_30_days}s), got {refresh_duration}s"
        
        print(f"✓ Refresh token expires in ~30 days (within tolerance)")
        
        # Step 7: Verify token contains user claims
        print(f"\nStep 5: Verifying token claims")
        
        assert access_payload.get('sub'), "Access token missing 'sub' claim"
        assert access_payload.get('email') == test_email, \
            f"Access token email mismatch: expected {test_email}, got {access_payload.get('email')}"
        assert 'role' in access_payload, "Access token missing 'role' claim"
        
        print(f"✓ Access token contains required claims:")
        print(f"  - sub (user ID): {access_payload.get('sub')}")
        print(f"  - email: {access_payload.get('email')}")
        print(f"  - role: {access_payload.get('role')}")
        
        print("\n✅ TEST 2 PASSED: User login returns valid JWT tokens")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_login_with_incorrect_password():
    """Test 3: Login fails with incorrect password (Feature #69)"""
    print("\n" + "="*80)
    print("TEST 3: Login Fails with Incorrect Password (Preview for Feature #69)")
    print("="*80)
    
    try:
        # Register a user
        test_email = f"test_wrong_pass_{int(time.time())}@example.com"
        test_password = "CorrectPass123!"
        
        print(f"Step 1: Registering test user: {test_email}")
        register_response = requests.post(
            f"{BASE_URL}/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test Wrong Pass User"
            },
            timeout=5
        )
        
        assert register_response.status_code == 201, "Registration failed"
        print(f"✓ User registered successfully")
        
        # Try to login with wrong password
        print(f"\nStep 2: Attempting login with incorrect password")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "email": test_email,
                "password": "WrongPassword123!"
            },
            timeout=5
        )
        
        print(f"✓ Login response status: {login_response.status_code}")
        
        assert login_response.status_code == 401, \
            f"Expected 401 Unauthorized, got {login_response.status_code}"
        
        print(f"✓ Login correctly rejected with 401 Unauthorized")
        
        error_data = login_response.json()
        print(f"✓ Error message: {error_data.get('detail', 'No detail provided')}")
        
        print("\n✅ TEST 3 PASSED: Login fails with incorrect password")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {str(e)}")
        return False


def test_login_with_nonexistent_email():
    """Test 4: Login fails with non-existent email (Feature #70)"""
    print("\n" + "="*80)
    print("TEST 4: Login Fails with Non-existent Email (Preview for Feature #70)")
    print("="*80)
    
    try:
        # Try to login with email that doesn't exist
        fake_email = f"nonexistent_{int(time.time())}@example.com"
        
        print(f"Step 1: Attempting login with non-existent email: {fake_email}")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "email": fake_email,
                "password": "SomePassword123!"
            },
            timeout=5
        )
        
        print(f"✓ Login response status: {login_response.status_code}")
        
        assert login_response.status_code == 401, \
            f"Expected 401 Unauthorized, got {login_response.status_code}"
        
        print(f"✓ Login correctly rejected with 401 Unauthorized")
        
        error_data = login_response.json()
        print(f"✓ Error message: {error_data.get('detail', 'No detail provided')}")
        
        print("\n✅ TEST 4 PASSED: Login fails with non-existent email")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("FEATURE #68 TEST SUITE: User Login with JWT Tokens")
    print("="*80)
    print(f"Testing against:")
    print(f"  - Backend: {BASE_URL}")
    print(f"  - Frontend: {FRONTEND_URL}")
    print(f"  - Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Run tests
    results.append(("Login Page Accessible", test_login_page_accessible()))
    results.append(("User Login Returns JWT Tokens", test_user_login_returns_jwt_tokens()))
    results.append(("Login Fails with Incorrect Password", test_login_with_incorrect_password()))
    results.append(("Login Fails with Non-existent Email", test_login_with_nonexistent_email()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Feature #68 is ready for production.")
        print("\nFeature #68 Status: ✅ PASSING")
        print("\nBonus: Features #69 and #70 are also working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review and fix.")
        return 1


if __name__ == "__main__":
    exit(main())
