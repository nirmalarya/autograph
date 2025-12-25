#!/usr/bin/env python3
"""
Feature #79 Validation: Password reset flow with valid token

Tests:
1. Register a new test user
2. Request password reset via /forgot-password
3. Get reset token from database
4. Reset password using /reset-password endpoint
5. Verify success response
6. Verify password updated in database
7. Verify reset token invalidated
8. Login with new password
9. Verify login succeeds
"""

import requests
import sys
import time
import uuid
import psycopg2
from datetime import datetime, timezone

# Configuration
AUTH_SERVICE_URL = "https://localhost:8085"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "autograph"
DB_USER = "autograph"
DB_PASSWORD = "autograph_dev_password"

# Disable SSL warnings for local testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def register_user(email, password):
    """Register a new user."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "username": email.split("@")[0]
        },
        verify=False
    )
    return response


def request_password_reset(email):
    """Request password reset."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/forgot-password",
        json={"email": email},
        verify=False
    )
    return response


def reset_password(token, new_password):
    """Reset password with token."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/reset-password",
        json={
            "token": token,
            "new_password": new_password
        },
        verify=False
    )
    return response


def login(email, password):
    """Login with email and password."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": email,
            "password": password
        },
        verify=False
    )
    return response


def get_verification_token_from_db(email):
    """Get email verification token from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        if not user_result:
            return None

        user_id = user_result[0]

        # Get verification token
        cursor.execute("""
            SELECT token
            FROM email_verification_tokens
            WHERE user_id = %s AND is_used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        result = cursor.fetchone()
        return result[0] if result else None

    finally:
        cursor.close()
        conn.close()


def verify_email(token):
    """Verify email with token."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/email/verify",
        json={"token": token},
        verify=False
    )
    return response


def get_reset_token_from_db(email):
    """Get reset token from database for user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_result = cursor.fetchone()
        if not user_result:
            return None

        user_id = user_result[0]

        # Get most recent unused reset token
        cursor.execute("""
            SELECT token, is_used, expires_at
            FROM password_reset_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        result = cursor.fetchone()
        return result if result else None

    finally:
        cursor.close()
        conn.close()


def verify_password_updated(email, old_password_hash):
    """Verify password hash has been updated in database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT password_hash FROM users WHERE email = %s",
            (email,)
        )
        result = cursor.fetchone()
        if not result:
            return False

        new_password_hash = result[0]

        # Password hash should be different from old hash
        return new_password_hash != old_password_hash

    finally:
        cursor.close()
        conn.close()


def verify_token_invalidated(token):
    """Verify reset token is marked as used."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT is_used, used_at FROM password_reset_tokens WHERE token = %s",
            (token,)
        )
        result = cursor.fetchone()
        if not result:
            return False

        is_used, used_at = result
        return is_used and used_at is not None

    finally:
        cursor.close()
        conn.close()


def main():
    """Run Feature #79 validation tests."""
    print("=" * 70)
    print("Feature #79: Password Reset Flow with Valid Token")
    print("=" * 70)

    # Generate unique test email
    test_id = str(uuid.uuid4())[:8]
    test_email = f"reset_flow_{test_id}@example.com"
    old_password = "OldPassword123!"
    new_password = "NewSecurePass123!"

    tests_passed = 0
    tests_total = 12

    try:
        # Test 1: Register test user
        print("\n[1/12] Registering test user...")
        response = register_user(test_email, old_password)
        if response.status_code == 201:
            print(f"✅ User registered: {test_email}")
            tests_passed += 1
        else:
            print(f"❌ Failed to register user: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        # Test 2: Verify email
        print("\n[2/12] Verifying email...")
        verification_token = get_verification_token_from_db(test_email)
        if verification_token:
            response = verify_email(verification_token)
            if response.status_code == 200:
                print(f"✅ Email verified")
                tests_passed += 1
            else:
                print(f"❌ Failed to verify email: {response.status_code}")
                return False
        else:
            print(f"❌ No verification token found")
            return False

        # Test 3: Request password reset
        print("\n[3/12] Requesting password reset...")
        response = request_password_reset(test_email)
        if response.status_code == 200:
            print(f"✅ Password reset requested")
            tests_passed += 1
        else:
            print(f"❌ Failed to request password reset: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        # Small delay for database consistency
        time.sleep(0.5)

        # Get old password hash for comparison
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = %s", (test_email,))
        old_password_hash = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        # Test 4: Get reset token from database
        print("\n[4/12] Getting reset token from database...")
        token_data = get_reset_token_from_db(test_email)
        if token_data:
            reset_token, is_used, expires_at = token_data
            print(f"✅ Reset token found: {reset_token[:20]}...")
            tests_passed += 1
        else:
            print(f"❌ No reset token found in database")
            return False

        # Test 5: Verify token is not used
        print("\n[5/12] Verifying token is not used...")
        if not is_used:
            print(f"✅ Token is unused (is_used=False)")
            tests_passed += 1
        else:
            print(f"❌ Token is already marked as used")
            return False

        # Test 6: Verify token is not expired
        print("\n[6/12] Verifying token is not expired...")
        now = datetime.now(timezone.utc)
        if now < expires_at:
            time_remaining = (expires_at - now).total_seconds()
            print(f"✅ Token is valid (expires in {int(time_remaining)} seconds)")
            tests_passed += 1
        else:
            print(f"❌ Token is already expired")
            return False

        # Test 7: Reset password with token
        print("\n[7/12] Resetting password with token...")
        response = reset_password(reset_token, new_password)
        if response.status_code == 200:
            print(f"✅ Password reset successful")
            tests_passed += 1
        else:
            print(f"❌ Failed to reset password: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        # Test 8: Verify success message
        print("\n[8/12] Verifying success message...")
        response_data = response.json()
        if "message" in response_data and "successfully" in response_data["message"].lower():
            print(f"✅ Success message received: {response_data['message']}")
            tests_passed += 1
        else:
            print(f"❌ No success message in response")
            print(f"Response: {response_data}")

        # Small delay for database update
        time.sleep(0.5)

        # Test 9: Verify password updated in database
        print("\n[9/12] Verifying password updated in database...")
        if verify_password_updated(test_email, old_password_hash):
            print(f"✅ Password hash updated in database")
            print(f"   - Password hash changed from old value")
            tests_passed += 1
        else:
            print(f"❌ Password not updated correctly in database")
            return False

        # Test 10: Verify reset token invalidated
        print("\n[10/12] Verifying reset token invalidated...")
        if verify_token_invalidated(reset_token):
            print(f"✅ Reset token marked as used")
            tests_passed += 1
        else:
            print(f"❌ Reset token not invalidated")
            return False

        # Test 11: Attempt to reuse token (should fail)
        print("\n[11/12] Attempting to reuse token (should fail)...")
        response = reset_password(reset_token, "AnotherPassword123!")
        if response.status_code == 400:
            print(f"✅ Token reuse blocked: {response.json().get('detail', '')}")
            tests_passed += 1
        else:
            print(f"❌ Token reuse not blocked: {response.status_code}")

        # Test 12: Login with new password
        print("\n[12/12] Logging in with new password...")
        response = login(test_email, new_password)
        if response.status_code == 200:
            print(f"✅ Login successful with new password")
            tests_passed += 1
        else:
            print(f"❌ Login failed with new password: {response.status_code}")
            print(f"Response: {response.text}")
            return False


        # Summary
        print("\n" + "=" * 70)
        print(f"VALIDATION RESULTS: {tests_passed}/{tests_total} tests passed")
        print("=" * 70)

        if tests_passed == tests_total:
            print("✅ Feature #79 - Password reset flow with valid token: PASSING")
            return True
        else:
            print(f"❌ Feature #79 - FAILING ({tests_passed}/{tests_total} tests passed)")
            return False

    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
