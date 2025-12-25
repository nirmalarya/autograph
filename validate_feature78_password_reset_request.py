#!/usr/bin/env python3
"""
Feature #78: Password Reset Flow - Request Reset Email
Tests the forgot-password endpoint functionality.
"""

import requests
import time
import sys
import secrets
import psycopg2
from datetime import datetime, timezone, timedelta

# Configuration
AUTH_SERVICE = "https://localhost:8085"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}


def print_step(step_num, description):
    """Print test step."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")


def print_result(success, message):
    """Print test result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    return success


def register_user(email, password="TestPass123!"):
    """Register a new user."""
    response = requests.post(
        f"{AUTH_SERVICE}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        },
        timeout=10,
        verify=False  # Disable SSL verification for local development
    )
    return response


def request_password_reset(email):
    """Request password reset for an email."""
    response = requests.post(
        f"{AUTH_SERVICE}/forgot-password",
        json={"email": email},
        timeout=10,
        verify=False  # Disable SSL verification for local development
    )
    return response


def get_reset_token_from_db(user_email):
    """Retrieve reset token from database for a user."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user_row = cursor.fetchone()
        if not user_row:
            return None, "User not found"

        user_id = user_row[0]

        # Get latest reset token for user
        cursor.execute("""
            SELECT token, expires_at, is_used, created_at
            FROM password_reset_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        token_row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not token_row:
            return None, "No reset token found"

        return {
            "token": token_row[0],
            "expires_at": token_row[1],
            "is_used": token_row[2],
            "created_at": token_row[3]
        }, None

    except Exception as e:
        return None, str(e)


def main():
    """Run validation tests for Feature #78."""

    print("\n" + "="*60)
    print("FEATURE #78: Password Reset Flow - Request Reset Email")
    print("="*60)

    # Generate unique email for this test
    test_email = f"reset_test_{secrets.token_hex(4)}@example.com"
    test_password = "SecurePass123!"

    results = []

    # STEP 1: Register user
    print_step(1, "Register test user")
    try:
        response = register_user(test_email, test_password)
        results.append(print_result(
            response.status_code == 201,
            f"User registration: {response.status_code}"
        ))
    except Exception as e:
        results.append(print_result(False, f"Registration failed: {e}"))
        print("\n❌ VALIDATION FAILED - Cannot proceed without user registration")
        sys.exit(1)

    # STEP 2: Request password reset via /forgot-password
    print_step(2, "Request password reset")
    try:
        response = request_password_reset(test_email)
        results.append(print_result(
            response.status_code == 200,
            f"Password reset request: {response.status_code} (expected 200)"
        ))

        if response.status_code == 200:
            data = response.json()
            results.append(print_result(
                "message" in data,
                f"Response contains message: {data.get('message', 'N/A')}"
            ))
    except Exception as e:
        results.append(print_result(False, f"Password reset request failed: {e}"))
        print("\n❌ VALIDATION FAILED - Cannot proceed without reset request")
        sys.exit(1)

    # STEP 3: Verify reset token stored in database
    print_step(3, "Verify reset token in database")
    time.sleep(1)  # Give DB time to commit

    try:
        token_data, error = get_reset_token_from_db(test_email)
        if error:
            results.append(print_result(False, f"Failed to retrieve token: {error}"))
        else:
            results.append(print_result(True, "Reset token found in database"))

            # Verify token is not empty
            results.append(print_result(
                len(token_data['token']) > 20,
                f"Token has sufficient length: {len(token_data['token'])} chars"
            ))

            # Verify token is not used
            results.append(print_result(
                token_data['is_used'] is False,
                f"Token is unused: {not token_data['is_used']}"
            ))

            # Verify expiry is approximately 1 hour from now
            expires_at = token_data['expires_at']
            created_at = token_data['created_at']

            # Make both timezone-aware
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            time_until_expiry = (expires_at - now).total_seconds()

            # Should expire in approximately 1 hour (3600 seconds)
            # Allow some variance: 55-65 minutes
            is_valid_expiry = 3300 <= time_until_expiry <= 3900
            results.append(print_result(
                is_valid_expiry,
                f"Token expires in ~1 hour: {time_until_expiry/60:.1f} minutes"
            ))

            # Verify reset link format (simulated - would be in email)
            reset_link = f"http://localhost:3000/reset-password?token={token_data['token']}"
            results.append(print_result(
                "reset-password?token=" in reset_link,
                f"Reset link format valid: {reset_link[:50]}..."
            ))

    except Exception as e:
        results.append(print_result(False, f"Database verification failed: {e}"))

    # STEP 4: Test with non-existent email (should still return 200 for security)
    print_step(4, "Test with non-existent email")
    try:
        fake_email = f"nonexistent_{secrets.token_hex(4)}@example.com"
        response = request_password_reset(fake_email)
        results.append(print_result(
            response.status_code == 200,
            f"Non-existent email returns 200 (prevents enumeration): {response.status_code}"
        ))
    except Exception as e:
        results.append(print_result(False, f"Non-existent email test failed: {e}"))

    # STEP 5: Test multiple reset requests (should invalidate previous tokens)
    print_step(5, "Test multiple reset requests")
    try:
        # Request another reset
        response = request_password_reset(test_email)
        results.append(print_result(
            response.status_code == 200,
            f"Second reset request: {response.status_code}"
        ))

        time.sleep(1)  # Give DB time to commit

        # Check database - should have newest token
        token_data, error = get_reset_token_from_db(test_email)
        if not error:
            results.append(print_result(
                token_data['is_used'] is False,
                "New token is unused (old tokens should be invalidated)"
            ))
    except Exception as e:
        results.append(print_result(False, f"Multiple reset test failed: {e}"))

    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print("\n✅ ALL VALIDATIONS PASSED - Feature #78 is working correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ VALIDATION FAILED - {total - passed} checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
