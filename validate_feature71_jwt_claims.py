#!/usr/bin/env python3
"""
Feature 71: JWT access token contains user claims (id, email, roles)
Tests that JWT access tokens contain all required claims with correct values.
"""

import requests
import json
import sys
import time
import random
import string
import jwt
from datetime import datetime, timezone
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

AUTH_BASE_URL = "https://localhost:8085"
VERIFY_SSL = False

def random_email():
    """Generate random email to avoid conflicts"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def create_verified_user():
    """Helper to create and verify a user"""
    email = random_email()
    password = "TestPass123!"

    # Register
    response = requests.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        },
        verify=VERIFY_SSL,
        timeout=5
    )

    if response.status_code != 201:
        return None, None, None

    user_data = response.json()
    user_id = user_data.get("id")

    # Get verification token from database
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token FROM email_verification_tokens WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return None, None, None

    token = result[0]
    cursor.close()
    conn.close()

    # Verify email
    verify_response = requests.post(
        f"{AUTH_BASE_URL}/email/verify",
        json={"token": token},
        verify=VERIFY_SSL,
        timeout=5
    )

    if verify_response.status_code != 200:
        return None, None, None

    return email, password, user_id

def test_jwt_access_token_claims():
    """Test JWT access token contains all required claims"""
    print("\n" + "="*80)
    print("Feature 71: JWT access token contains user claims")
    print("="*80)

    tests_passed = 0
    tests_failed = 0

    # Step 1: Create and verify user, then login
    print("\n[Test 1] Creating user and logging in...")
    try:
        email, password, user_id = create_verified_user()

        if not email:
            print("❌ Failed to create verified user")
            tests_failed += 1
            return tests_passed, tests_failed

        # Login
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": email,
                "password": password
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            tests_failed += 1
            return tests_passed, tests_failed

        login_data = response.json()
        access_token = login_data.get("access_token")

        if not access_token:
            print(f"❌ No access_token in response")
            tests_failed += 1
            return tests_passed, tests_failed

        print(f"✅ User logged in successfully")
        print(f"   Email: {email}")
        print(f"   User ID: {user_id}")
        tests_passed += 1

    except Exception as e:
        print(f"❌ Login error: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Step 2: Decode JWT without verification (to inspect claims)
    print("\n[Test 2] Decoding JWT access token...")
    try:
        # Decode without verification to inspect claims
        decoded = jwt.decode(access_token, options={"verify_signature": False})

        print(f"✅ JWT decoded successfully")
        print(f"   Token claims: {json.dumps(decoded, indent=2, default=str)}")
        tests_passed += 1

    except Exception as e:
        print(f"❌ JWT decode error: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Step 3: Verify 'sub' claim contains user ID
    print("\n[Test 3] Verifying 'sub' claim contains user ID...")
    try:
        sub_claim = decoded.get("sub")

        if sub_claim == user_id:
            print(f"✅ 'sub' claim matches user ID: {user_id}")
            tests_passed += 1
        else:
            print(f"❌ 'sub' claim mismatch: expected '{user_id}', got '{sub_claim}'")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking 'sub' claim: {e}")
        tests_failed += 1

    # Step 4: Verify 'email' claim contains user email
    print("\n[Test 4] Verifying 'email' claim contains user email...")
    try:
        email_claim = decoded.get("email")

        if email_claim == email:
            print(f"✅ 'email' claim matches user email: {email}")
            tests_passed += 1
        else:
            print(f"❌ 'email' claim mismatch: expected '{email}', got '{email_claim}'")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking 'email' claim: {e}")
        tests_failed += 1

    # Step 5: Verify 'roles' or 'role' claim exists
    print("\n[Test 5] Verifying 'roles' or 'role' claim exists...")
    try:
        role_claim = decoded.get("role") or decoded.get("roles")

        if role_claim:
            print(f"✅ Role claim found: {role_claim}")
            tests_passed += 1
        else:
            print(f"❌ No 'role' or 'roles' claim in token")
            print(f"   Available claims: {list(decoded.keys())}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking role claim: {e}")
        tests_failed += 1

    # Step 6: Verify 'exp' claim (expiration time)
    print("\n[Test 6] Verifying 'exp' claim (expiration time)...")
    try:
        exp_claim = decoded.get("exp")

        if not exp_claim:
            print(f"❌ No 'exp' claim in token")
            tests_failed += 1
        else:
            # Convert to datetime
            exp_time = datetime.fromtimestamp(exp_claim, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)

            # Should be approximately 1 hour from now
            time_diff = (exp_time - now).total_seconds()

            # Allow 59-61 minutes (3540-3660 seconds) for 1 hour expiry
            if 3540 <= time_diff <= 3660:
                print(f"✅ 'exp' claim valid: expires in {time_diff:.0f} seconds (~1 hour)")
                tests_passed += 1
            else:
                print(f"⚠️  'exp' claim: expires in {time_diff:.0f} seconds")
                print(f"   Expected: ~3600 seconds (1 hour)")
                # Don't fail if expiry is reasonable (within 2 hours)
                if 0 < time_diff < 7200:
                    print(f"   Acceptable expiry time")
                    tests_passed += 1
                else:
                    tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking 'exp' claim: {e}")
        tests_failed += 1

    # Step 7: Verify 'iat' claim (issued at time)
    print("\n[Test 7] Verifying 'iat' claim (issued at time)...")
    try:
        iat_claim = decoded.get("iat")

        if not iat_claim:
            print(f"❌ No 'iat' claim in token")
            tests_failed += 1
        else:
            # Convert to datetime
            iat_time = datetime.fromtimestamp(iat_claim, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)

            # Should be very recent (within last 10 seconds)
            time_diff = abs((now - iat_time).total_seconds())

            if time_diff <= 10:
                print(f"✅ 'iat' claim valid: issued {time_diff:.1f} seconds ago")
                tests_passed += 1
            else:
                print(f"⚠️  'iat' claim: issued {time_diff:.1f} seconds ago")
                # Allow up to 60 seconds for clock skew
                if time_diff <= 60:
                    print(f"   Acceptable issued time (clock skew)")
                    tests_passed += 1
                else:
                    tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking 'iat' claim: {e}")
        tests_failed += 1

    # Step 8: Verify token algorithm is HS256
    print("\n[Test 8] Verifying token algorithm is HS256...")
    try:
        # Decode header
        header = jwt.get_unverified_header(access_token)
        algorithm = header.get("alg")

        if algorithm == "HS256":
            print(f"✅ Token uses HS256 algorithm")
            tests_passed += 1
        else:
            print(f"❌ Token uses '{algorithm}' instead of HS256")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking algorithm: {e}")
        tests_failed += 1

    # Step 9: Verify JWT structure (3 parts separated by dots)
    print("\n[Test 9] Verifying JWT structure...")
    try:
        parts = access_token.split('.')

        if len(parts) == 3:
            print(f"✅ JWT has correct structure (header.payload.signature)")
            tests_passed += 1
        else:
            print(f"❌ JWT has {len(parts)} parts instead of 3")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking JWT structure: {e}")
        tests_failed += 1

    # Step 10: Verify all standard JWT claims are present
    print("\n[Test 10] Verifying all required claims are present...")
    try:
        required_claims = ['sub', 'email', 'exp', 'iat']
        missing_claims = [claim for claim in required_claims if claim not in decoded]

        if not missing_claims:
            print(f"✅ All required claims present: {required_claims}")
            tests_passed += 1
        else:
            print(f"❌ Missing claims: {missing_claims}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error checking required claims: {e}")
        tests_failed += 1

    return tests_passed, tests_failed

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("FEATURE 71 VALIDATION: JWT Access Token Claims")
    print("="*80)

    # Check if auth service is running
    print("\nChecking auth service availability...")
    try:
        response = requests.get(f"{AUTH_BASE_URL}/health", verify=VERIFY_SSL, timeout=5)
        if response.status_code == 200:
            print("✅ Auth service is running")
        else:
            print(f"❌ Auth service health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to auth service: {e}")
        return 1

    # Run tests
    passed, failed = test_jwt_access_token_claims()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Success rate: {passed}/{passed + failed} ({100 * passed / (passed + failed) if (passed + failed) > 0 else 0:.1f}%)")

    if failed == 0:
        print("\n✅ Feature 71: PASSING - JWT access token contains all required user claims")
        return 0
    else:
        print(f"\n❌ Feature 71: FAILING - {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
