#!/usr/bin/env python3
"""
Test suite for Features #71, #72, #74: JWT Token Claims and Expiry

This test verifies:
- Feature #71: JWT access token contains user claims (id, email, roles)
- Feature #72: JWT access token expires after 1 hour
- Feature #74: JWT refresh token expires after 30 days
"""

import requests
import time
import jwt
from datetime import datetime

BASE_URL = "http://localhost:8085"

def test_feature_71_jwt_access_token_contains_claims():
    """Feature #71: JWT access token contains user claims (id, email, roles)"""
    print("\n" + "="*80)
    print("FEATURE #71: JWT Access Token Contains User Claims")
    print("="*80)
    
    try:
        # Register and login
        test_email = f"test_claims_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        print(f"Step 1: Registering user: {test_email}")
        requests.post(
            f"{BASE_URL}/register",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        print(f"Step 2: Logging in")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
        
        data = login_response.json()
        access_token = data["access_token"]
        
        print(f"Step 3: Decoding access token")
        payload = jwt.decode(access_token, options={"verify_signature": False})
        
        # Verify claims
        print(f"\nVerifying claims:")
        
        assert "sub" in payload, "Missing 'sub' claim (user ID)"
        print(f"✓ sub (user ID): {payload['sub']}")
        
        assert "email" in payload, "Missing 'email' claim"
        assert payload["email"] == test_email, f"Email mismatch: {payload['email']} != {test_email}"
        print(f"✓ email: {payload['email']}")
        
        assert "role" in payload, "Missing 'role' claim"
        print(f"✓ role: {payload['role']}")
        
        print("\n✅ FEATURE #71 PASSED: Access token contains all required claims (id, email, role)")
        return True
        
    except Exception as e:
        print(f"\n❌ FEATURE #71 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_72_jwt_access_token_expires_1_hour():
    """Feature #72: JWT access token expires after 1 hour"""
    print("\n" + "="*80)
    print("FEATURE #72: JWT Access Token Expires After 1 Hour")
    print("="*80)
    
    try:
        # Register and login
        test_email = f"test_expiry_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        print(f"Step 1: Registering user: {test_email}")
        requests.post(
            f"{BASE_URL}/register",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        print(f"Step 2: Logging in")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
        
        data = login_response.json()
        access_token = data["access_token"]
        
        print(f"Step 3: Checking token expiry")
        payload = jwt.decode(access_token, options={"verify_signature": False})
        
        assert "exp" in payload, "Missing 'exp' claim"
        assert "iat" in payload, "Missing 'iat' claim"
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        duration = (exp_time - iat_time).total_seconds()
        
        print(f"\nToken timing:")
        print(f"  Issued at: {iat_time}")
        print(f"  Expires at: {exp_time}")
        print(f"  Duration: {duration} seconds ({duration/3600} hours)")
        
        # Verify 1 hour expiry (3600 seconds, allow 1 minute tolerance)
        expected_duration = 3600
        tolerance = 60
        
        assert expected_duration - tolerance <= duration <= expected_duration + tolerance, \
            f"Token should expire in 1 hour (3600s ± 60s), got {duration}s"
        
        print(f"\n✓ Access token expires in 1 hour (within tolerance)")
        print("\n✅ FEATURE #72 PASSED: Access token expires after 1 hour")
        return True
        
    except Exception as e:
        print(f"\n❌ FEATURE #72 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_74_jwt_refresh_token_expires_30_days():
    """Feature #74: JWT refresh token expires after 30 days"""
    print("\n" + "="*80)
    print("FEATURE #74: JWT Refresh Token Expires After 30 Days")
    print("="*80)
    
    try:
        # Register and login
        test_email = f"test_refresh_{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        print(f"Step 1: Registering user: {test_email}")
        requests.post(
            f"{BASE_URL}/register",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        print(f"Step 2: Logging in")
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={"email": test_email, "password": test_password},
            timeout=5
        )
        
        assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
        
        data = login_response.json()
        refresh_token = data["refresh_token"]
        
        print(f"Step 3: Checking refresh token expiry")
        payload = jwt.decode(refresh_token, options={"verify_signature": False})
        
        assert "exp" in payload, "Missing 'exp' claim"
        assert "iat" in payload, "Missing 'iat' claim"
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        duration = (exp_time - iat_time).total_seconds()
        
        print(f"\nToken timing:")
        print(f"  Issued at: {iat_time}")
        print(f"  Expires at: {exp_time}")
        print(f"  Duration: {duration} seconds ({duration/(24*3600)} days)")
        
        # Verify 30 days expiry (2,592,000 seconds, allow 1 hour tolerance)
        expected_duration = 30 * 24 * 3600  # 2,592,000 seconds
        tolerance = 3600  # 1 hour
        
        assert expected_duration - tolerance <= duration <= expected_duration + tolerance, \
            f"Token should expire in 30 days ({expected_duration}s ± {tolerance}s), got {duration}s"
        
        print(f"\n✓ Refresh token expires in 30 days (within tolerance)")
        print("\n✅ FEATURE #74 PASSED: Refresh token expires after 30 days")
        return True
        
    except Exception as e:
        print(f"\n❌ FEATURE #74 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("JWT TOKEN FEATURES TEST SUITE")
    print("="*80)
    print(f"Testing Features #71, #72, #74")
    print(f"Backend: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Run tests
    results.append(("Feature #71: JWT access token contains user claims", test_feature_71_jwt_access_token_contains_claims()))
    results.append(("Feature #72: JWT access token expires after 1 hour", test_feature_72_jwt_access_token_expires_1_hour()))
    results.append(("Feature #74: JWT refresh token expires after 30 days", test_feature_74_jwt_refresh_token_expires_30_days()))
    
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
        print("\n🎉 ALL TESTS PASSED! Features #71, #72, #74 are ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review and fix.")
        return 1


if __name__ == "__main__":
    exit(main())
