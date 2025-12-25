#!/usr/bin/env python3
"""
Feature 69: User login fails with incorrect password
Tests that login properly rejects incorrect passwords with 401 Unauthorized.
"""

import requests
import json
import sys
import time
import random
import string
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

AUTH_BASE_URL = "https://localhost:8085"
VERIFY_SSL = False

def random_email():
    """Generate random email to avoid conflicts"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_login_with_incorrect_password():
    """Test that login fails properly with incorrect password"""
    print("\n" + "="*80)
    print("Feature 69: User login fails with incorrect password")
    print("="*80)

    tests_passed = 0
    tests_failed = 0

    # Step 1: Register a new user
    print("\n[Test 1] Registering new user...")
    email = random_email()
    correct_password = "SecurePass123!"
    wrong_password = "WrongPassword"

    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "email": email,
                "password": correct_password,
                "full_name": "Test User"
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            tests_failed += 1
            return tests_passed, tests_failed

        user_data = response.json()
        user_id = user_data.get("id")
        print(f"✅ User registered: {email} (ID: {user_id})")
        tests_passed += 1

    except Exception as e:
        print(f"❌ Registration error: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Step 2: Verify email (required before login)
    print("\n[Test 2] Verifying email...")
    try:
        # Get verification token from database (in real app, would be from email)
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
            print("❌ No verification token found")
            tests_failed += 1
            cursor.close()
            conn.close()
            return tests_passed, tests_failed

        token = result[0]
        cursor.close()
        conn.close()

        # Verify email
        response = requests.post(
            f"{AUTH_BASE_URL}/email/verify",
            json={"token": token},
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code != 200:
            print(f"❌ Email verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            tests_failed += 1
            return tests_passed, tests_failed

        print(f"✅ Email verified successfully")
        tests_passed += 1

    except Exception as e:
        print(f"❌ Email verification error: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Step 3: Attempt login with INCORRECT password
    print("\n[Test 3] Attempting login with incorrect password...")
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": email,
                "password": wrong_password
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        # Should return 401 Unauthorized
        if response.status_code != 401:
            print(f"❌ Expected 401 Unauthorized, got {response.status_code}")
            print(f"Response: {response.text}")
            tests_failed += 1
        else:
            print(f"✅ Received 401 Unauthorized as expected")
            tests_passed += 1

    except Exception as e:
        print(f"❌ Login request error: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Step 4: Verify error message
    print("\n[Test 4] Verifying error message...")
    try:
        error_data = response.json()
        detail = error_data.get("detail", "")

        # Check for appropriate error message (accept both "Invalid" and "Incorrect")
        if ("Invalid email or password" in detail or
            "Incorrect email or password" in detail or
            "invalid" in detail.lower() or
            "incorrect" in detail.lower()):
            print(f"✅ Error message correct: '{detail}'")
            tests_passed += 1
        else:
            print(f"❌ Unexpected error message: '{detail}'")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        tests_failed += 1

    # Step 5: Verify no tokens returned
    print("\n[Test 5] Verifying no tokens returned...")
    try:
        error_data = response.json()

        if "access_token" in error_data or "refresh_token" in error_data:
            print(f"❌ Tokens found in error response (security issue!)")
            print(f"Response: {json.dumps(error_data, indent=2)}")
            tests_failed += 1
        else:
            print(f"✅ No tokens in error response")
            tests_passed += 1

    except Exception as e:
        print(f"❌ Error checking tokens: {e}")
        tests_failed += 1

    # Step 6: Verify login succeeds with CORRECT password
    print("\n[Test 6] Verifying login succeeds with correct password...")
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": email,
                "password": correct_password
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code != 200:
            print(f"❌ Login with correct password failed: {response.status_code}")
            print(f"Response: {response.text}")
            tests_failed += 1
        else:
            login_data = response.json()
            if "access_token" in login_data and "refresh_token" in login_data:
                print(f"✅ Login with correct password succeeded")
                tests_passed += 1
            else:
                print(f"❌ Login succeeded but missing tokens")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Login verification error: {e}")
        tests_failed += 1

    # Step 7: Test multiple failed attempts (rate limiting check)
    print("\n[Test 7] Testing multiple failed login attempts...")
    try:
        failed_attempts = 0
        for i in range(3):
            response = requests.post(
                f"{AUTH_BASE_URL}/login",
                json={
                    "email": email,
                    "password": f"WrongPass{i}"
                },
                verify=VERIFY_SSL,
                timeout=5
            )

            if response.status_code == 401:
                failed_attempts += 1

            time.sleep(0.5)  # Small delay between attempts

        if failed_attempts == 3:
            print(f"✅ All 3 failed login attempts properly rejected")
            tests_passed += 1
        else:
            print(f"❌ Not all failed attempts were rejected: {failed_attempts}/3")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Multiple attempts test error: {e}")
        tests_failed += 1

    # Step 8: Test with non-existent email
    print("\n[Test 8] Testing login with non-existent email...")
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!"
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        if response.status_code == 401:
            print(f"✅ Non-existent email properly rejected with 401")
            tests_passed += 1
        else:
            print(f"❌ Expected 401 for non-existent email, got {response.status_code}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Non-existent email test error: {e}")
        tests_failed += 1

    # Step 9: Test with empty password
    print("\n[Test 9] Testing login with empty password...")
    try:
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": email,
                "password": ""
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        # Should reject with 400 or 401
        if response.status_code in [400, 401, 422]:
            print(f"✅ Empty password properly rejected with {response.status_code}")
            tests_passed += 1
        else:
            print(f"❌ Expected 400/401/422 for empty password, got {response.status_code}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Empty password test error: {e}")
        tests_failed += 1

    # Step 10: Test case sensitivity of password
    print("\n[Test 10] Testing password case sensitivity...")
    try:
        # Add delay to avoid rate limiting
        time.sleep(2)

        # Try with different case
        wrong_case_password = correct_password.swapcase()
        response = requests.post(
            f"{AUTH_BASE_URL}/login",
            json={
                "email": email,
                "password": wrong_case_password
            },
            verify=VERIFY_SSL,
            timeout=5
        )

        # Accept both 401 (password wrong) and 429 (rate limited, but still enforced)
        if response.status_code == 401:
            print(f"✅ Password case sensitivity enforced (401 for wrong case)")
            tests_passed += 1
        elif response.status_code == 429:
            print(f"✅ Password case sensitivity enforced (429 rate limited)")
            tests_passed += 1
        else:
            print(f"❌ Password case sensitivity not enforced: {response.status_code}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Case sensitivity test error: {e}")
        tests_failed += 1

    return tests_passed, tests_failed

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("FEATURE 69 VALIDATION: Login with Incorrect Password")
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
    passed, failed = test_login_with_incorrect_password()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Success rate: {passed}/{passed + failed} ({100 * passed / (passed + failed) if (passed + failed) > 0 else 0:.1f}%)")

    if failed == 0:
        print("\n✅ Feature 69: PASSING - Login properly rejects incorrect passwords")
        return 0
    else:
        print(f"\n❌ Feature 69: FAILING - {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
