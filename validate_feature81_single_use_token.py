#!/usr/bin/env python3
"""
Feature #81 Validation: Password reset token can only be used once

Tests:
1. Request password reset
2. Get reset token
3. Reset password successfully (first use)
4. Attempt to use same token again (second use)
5. Verify 400 Bad Request response
6. Verify error message contains 'already used' or 'used'
7. Verify token is marked as used in database
"""

import requests
import json
import time
import sys
import psycopg2
from datetime import datetime, timedelta, timezone
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Service URLs
AUTH_SERVICE_URL = "https://localhost:8085"

# Test configuration
TEST_EMAIL = f"single_use_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!"
NEW_PASSWORD_1 = "NewPassword456!"
NEW_PASSWORD_2 = "AnotherPassword789!"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def print_test_header(test_name):
    """Print formatted test header."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")

def print_result(success, message):
    """Print test result."""
    symbol = "✅" if success else "❌"
    print(f"{symbol} {message}")
    return success

def get_db_connection():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(**DB_CONFIG)

def get_token_from_db(email):
    """Get the most recent reset token for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT prt.token, prt.is_used, prt.used_at, prt.expires_at
            FROM password_reset_tokens prt
            JOIN users u ON prt.user_id = u.id
            WHERE u.email = %s
            ORDER BY prt.created_at DESC
            LIMIT 1
            """,
            (email,)
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return {
                "token": result[0],
                "is_used": result[1],
                "used_at": result[2],
                "expires_at": result[3]
            }
        return None

    except Exception as e:
        print(f"  → Database error: {str(e)}")
        return None

def main():
    """Run Feature #81 validation tests."""

    print("\n" + "="*70)
    print("FEATURE #81 VALIDATION: Password Reset Token Single Use")
    print("="*70)

    results = []
    reset_token = None

    # Test 1: Register user
    print_test_header("Test 1: User Registration")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Single Use Token Test User"
            },
            verify=False
        )

        if response.status_code == 201:
            results.append(print_result(True, "User registered successfully"))
        else:
            results.append(print_result(False, f"Registration failed: {response.status_code}"))
            print(f"  Response: {response.text}")
            sys.exit(1)

    except Exception as e:
        results.append(print_result(False, f"Registration error: {str(e)}"))
        sys.exit(1)

    # Test 2: Verify email
    print_test_header("Test 2: Email Verification")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token FROM email_verification_tokens
            WHERE user_id = (SELECT id FROM users WHERE email = %s)
            ORDER BY created_at DESC LIMIT 1
            """,
            (TEST_EMAIL,)
        )
        verification_token = cursor.fetchone()
        cursor.close()
        conn.close()

        if verification_token:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/email/verify",
                json={"token": verification_token[0]},
                verify=False
            )

            if response.status_code == 200:
                results.append(print_result(True, "Email verified successfully"))
            else:
                results.append(print_result(False, f"Email verification failed: {response.status_code}"))
        else:
            results.append(print_result(False, "Could not retrieve verification token"))

    except Exception as e:
        results.append(print_result(False, f"Email verification error: {str(e)}"))

    # Test 3: Request password reset
    print_test_header("Test 3: Request Password Reset")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/forgot-password",
            json={"email": TEST_EMAIL},
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "Password reset requested successfully"))
        else:
            results.append(print_result(False, f"Password reset request failed: {response.status_code}"))
            print(f"  Response: {response.text}")

    except Exception as e:
        results.append(print_result(False, f"Password reset request error: {str(e)}"))

    # Test 4: Get token from database
    print_test_header("Test 4: Retrieve Reset Token from Database")
    try:
        time.sleep(0.5)  # Small delay to ensure token is created
        token_info = get_token_from_db(TEST_EMAIL)

        if token_info and token_info["token"]:
            reset_token = token_info["token"]
            results.append(print_result(True, f"Retrieved reset token: {reset_token[:20]}..."))
            print(f"  → Token is_used: {token_info['is_used']}")
            print(f"  → Token used_at: {token_info['used_at']}")
            print(f"  → Token expires_at: {token_info['expires_at']}")
        else:
            results.append(print_result(False, "Could not retrieve reset token"))
            sys.exit(1)

    except Exception as e:
        results.append(print_result(False, f"Token retrieval error: {str(e)}"))
        sys.exit(1)

    # Test 5: Use token to reset password (first use - should succeed)
    print_test_header("Test 5: Use Token to Reset Password (First Use)")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/reset-password",
            json={
                "token": reset_token,
                "new_password": NEW_PASSWORD_1
            },
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "Password reset successful (first use)"))
            print(f"  → Password updated successfully")
        else:
            results.append(print_result(False, f"Password reset failed: {response.status_code}"))
            print(f"  Response: {response.text}")
            sys.exit(1)

    except Exception as e:
        results.append(print_result(False, f"Password reset error: {str(e)}"))
        sys.exit(1)

    # Test 6: Verify token is marked as used in database
    print_test_header("Test 6: Verify Token Marked as Used in Database")
    try:
        time.sleep(0.5)  # Small delay to ensure DB is updated
        token_info = get_token_from_db(TEST_EMAIL)

        if token_info:
            if token_info["is_used"] == True:
                results.append(print_result(True, "Token correctly marked as used in database"))
                print(f"  → is_used: {token_info['is_used']}")
                print(f"  → used_at: {token_info['used_at']}")
            else:
                results.append(print_result(False, f"Token not marked as used: is_used={token_info['is_used']}"))
        else:
            results.append(print_result(False, "Could not retrieve token info"))

    except Exception as e:
        results.append(print_result(False, f"Token verification error: {str(e)}"))

    # Test 7: Attempt to use same token again (should fail)
    print_test_header("Test 7: Attempt to Reuse Token (Should Fail)")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/reset-password",
            json={
                "token": reset_token,
                "new_password": NEW_PASSWORD_2
            },
            verify=False
        )

        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get("detail", "").lower()

            if "used" in error_message or "already" in error_message:
                results.append(print_result(True, "Token reuse correctly prevented"))
                print(f"  → Error message: {response_data.get('detail')}")
            else:
                results.append(print_result(False, f"Wrong error message: {response_data.get('detail')}"))
        else:
            results.append(print_result(False, f"Expected 400, got {response.status_code}"))
            print(f"  Response: {response.text}")

    except Exception as e:
        results.append(print_result(False, f"Token reuse test error: {str(e)}"))

    # Test 8: Verify password was NOT changed by second attempt
    print_test_header("Test 8: Verify Password NOT Changed by Reuse Attempt")
    try:
        # Try to login with NEW_PASSWORD_2 (should fail)
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": TEST_EMAIL,
                "password": NEW_PASSWORD_2
            },
            verify=False
        )

        if response.status_code != 200:
            results.append(print_result(True, "Password correctly NOT changed by reuse attempt"))
            print(f"  → Login with second password failed as expected")
        else:
            results.append(print_result(False, "Password was changed by reuse attempt (security issue!)"))

    except Exception as e:
        results.append(print_result(False, f"Login verification error: {str(e)}"))

    # Test 9: Verify original password (NEW_PASSWORD_1) still works
    print_test_header("Test 9: Verify Original Reset Password Still Works")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": TEST_EMAIL,
                "password": NEW_PASSWORD_1
            },
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "Login successful with first reset password"))
        else:
            results.append(print_result(False, f"Login failed: {response.status_code}"))
            print(f"  Response: {response.text}")

    except Exception as e:
        results.append(print_result(False, f"Login error: {str(e)}"))

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(results)

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n✅ ALL TESTS PASSED - Feature #81 is working correctly!")
        print("\nSecurity verification:")
        print("  ✅ Tokens can only be used once")
        print("  ✅ Reuse attempts are blocked with 400 error")
        print("  ✅ Tokens are marked as used in database")
        print("  ✅ Password is not changed on reuse attempt")
        sys.exit(0)
    else:
        print(f"\n❌ {total_tests - passed_tests} TEST(S) FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
