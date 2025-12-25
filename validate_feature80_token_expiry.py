#!/usr/bin/env python3
"""
Feature #80 Validation: Password reset token expires after 1 hour

Tests:
1. Request password reset
2. Get reset token from database
3. Manually expire token by updating expires_at to past
4. Attempt to reset password with expired token
5. Verify 400 Bad Request response
6. Verify error message contains 'expired'
7. Request new reset token
8. Verify new token works within expiry time
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
TEST_EMAIL = f"token_expiry_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!"
NEW_PASSWORD = "NewSecurePassword456!"

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

def expire_token_in_db(token):
    """Manually expire token by setting expires_at to past."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Set expires_at to 2 hours ago
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET expires_at = %s
            WHERE token = %s AND is_used = FALSE
            RETURNING id, expires_at
            """,
            (past_time, token)
        )

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if result:
            print(f"  → Token expired at: {result[1]}")
            return True
        else:
            print(f"  → Token not found or already used")
            return False

    except Exception as e:
        print(f"  → Database error: {str(e)}")
        return False

def get_token_from_db(email):
    """Get the most recent unused reset token for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT prt.token, prt.expires_at, prt.is_used
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
                "expires_at": result[1],
                "is_used": result[2]
            }
        return None

    except Exception as e:
        print(f"  → Database error: {str(e)}")
        return None

def main():
    """Run Feature #80 validation tests."""

    print("\n" + "="*70)
    print("FEATURE #80 VALIDATION: Password Reset Token Expiry (1 Hour)")
    print("="*70)

    results = []

    # Test 1: Register user
    print_test_header("Test 1: User Registration")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Token Expiry Test User"
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
        # Get verification token from database
        token_data = get_token_from_db(TEST_EMAIL)

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

    # Test 3: Request password reset (first time)
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
        token_info = get_token_from_db(TEST_EMAIL)

        if token_info and token_info["token"]:
            reset_token = token_info["token"]
            results.append(print_result(True, f"Retrieved reset token: {reset_token[:20]}..."))
            print(f"  → Token expires at: {token_info['expires_at']}")
            print(f"  → Token used: {token_info['is_used']}")
        else:
            results.append(print_result(False, "Could not retrieve reset token"))
            sys.exit(1)

    except Exception as e:
        results.append(print_result(False, f"Token retrieval error: {str(e)}"))
        sys.exit(1)

    # Test 5: Manually expire the token
    print_test_header("Test 5: Manually Expire Token")
    try:
        if expire_token_in_db(reset_token):
            results.append(print_result(True, "Token manually expired in database"))
        else:
            results.append(print_result(False, "Failed to expire token"))

    except Exception as e:
        results.append(print_result(False, f"Token expiry error: {str(e)}"))

    # Test 6: Attempt to use expired token
    print_test_header("Test 6: Use Expired Token (Should Fail)")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/reset-password",
            json={
                "token": reset_token,
                "new_password": NEW_PASSWORD
            },
            verify=False
        )

        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get("detail", "").lower()

            if "expired" in error_message:
                results.append(print_result(True, "Expired token correctly rejected"))
                print(f"  → Error message: {response_data.get('detail')}")
            else:
                results.append(print_result(False, f"Wrong error message: {response_data.get('detail')}"))
        else:
            results.append(print_result(False, f"Expected 400, got {response.status_code}"))
            print(f"  Response: {response.text}")

    except Exception as e:
        results.append(print_result(False, f"Expired token test error: {str(e)}"))

    # Test 7: Request new reset token
    print_test_header("Test 7: Request New Reset Token")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/forgot-password",
            json={"email": TEST_EMAIL},
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "New password reset requested successfully"))

            # Get new token from database
            time.sleep(0.5)  # Small delay to ensure token is created
            new_token_info = get_token_from_db(TEST_EMAIL)

            if new_token_info and new_token_info["token"]:
                new_reset_token = new_token_info["token"]
                print(f"  → New token: {new_reset_token[:20]}...")
                print(f"  → New token expires at: {new_token_info['expires_at']}")
            else:
                results.append(print_result(False, "Could not retrieve new reset token"))
                sys.exit(1)
        else:
            results.append(print_result(False, f"New password reset request failed: {response.status_code}"))
            sys.exit(1)

    except Exception as e:
        results.append(print_result(False, f"New password reset request error: {str(e)}"))
        sys.exit(1)

    # Test 8: Use new token successfully (within expiry)
    print_test_header("Test 8: Use New Token Within Expiry Time")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/reset-password",
            json={
                "token": new_reset_token,
                "new_password": NEW_PASSWORD
            },
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "Password reset successful with new token"))
            print(f"  → Password updated successfully")
        else:
            results.append(print_result(False, f"Password reset failed: {response.status_code}"))
            print(f"  Response: {response.text}")

    except Exception as e:
        results.append(print_result(False, f"Password reset error: {str(e)}"))

    # Test 9: Verify new password works
    print_test_header("Test 9: Login with New Password")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": TEST_EMAIL,
                "password": NEW_PASSWORD
            },
            verify=False
        )

        if response.status_code == 200:
            results.append(print_result(True, "Login successful with new password"))
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
        print("\n✅ ALL TESTS PASSED - Feature #80 is working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ {total_tests - passed_tests} TEST(S) FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
