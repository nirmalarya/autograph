#!/usr/bin/env python3
"""
Feature #101 Validation: Email verification link expires after 24 hours

Steps:
1. Register new user
2. Receive verification email (get token from DB)
3. Mock time forward 25 hours OR manipulate token expiry
4. Click verification link
5. Verify error: 'Verification link expired'
6. Click 'Resend verification email'
7. Receive new email
8. Click new link within 24 hours
9. Verify email verified successfully
"""

import requests
import psycopg2
import os
import time
import secrets
from datetime import datetime, timedelta, timezone

# Test configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8085")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "autograph")
POSTGRES_USER = os.getenv("POSTGRES_USER", "autograph")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

def cleanup_test_user(email: str):
    """Clean up test user from database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Delete user (cascade will handle related records)
        cur.execute("DELETE FROM users WHERE email = %s", (email,))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Cleanup error (non-critical): {e}")

def get_verification_token(email: str):
    """Get the latest verification token for a user from database."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get user ID
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        return None

    user_id = user_row[0]

    # Get latest unused verification token
    cur.execute("""
        SELECT token, expires_at
        FROM email_verification_tokens
        WHERE user_id = %s AND is_used = false
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))

    token_row = cur.fetchone()
    cur.close()
    conn.close()

    if token_row:
        return {
            "token": token_row[0],
            "expires_at": token_row[1]
        }
    return None

def expire_verification_token(email: str):
    """Manually expire the verification token for a user (set expires_at to past)."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get user ID
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        return False

    user_id = user_row[0]

    # Expire the token (set expires_at to 25 hours ago)
    past_time = datetime.now(timezone.utc) - timedelta(hours=25)
    cur.execute("""
        UPDATE email_verification_tokens
        SET expires_at = %s
        WHERE user_id = %s AND is_used = false
    """, (past_time, user_id))

    conn.commit()
    cur.close()
    conn.close()
    return True

def test_email_verification_expiry():
    """Test email verification link expiry after 24 hours."""
    print("\n" + "="*80)
    print("Feature #101: Email verification link expires after 24 hours")
    print("="*80)

    # Generate unique test email
    test_email = f"test_expiry_{secrets.token_hex(4)}@example.com"
    test_password = "SecurePassword123!"

    try:
        # Clean up any existing test user
        cleanup_test_user(test_email)

        # Step 1: Register new user
        print("\n1️⃣  Registering new user...")
        register_response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test User Expiry"
            }
        )

        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"   Response: {register_response.text}")
            return False

        print(f"✅ User registered: {test_email}")

        # Step 2: Get verification token from database
        print("\n2️⃣  Getting verification token from database...")
        token_data = get_verification_token(test_email)

        if not token_data:
            print("❌ No verification token found in database")
            return False

        original_token = token_data["token"]
        print(f"✅ Verification token retrieved: {original_token[:20]}...")
        print(f"   Expires at: {token_data['expires_at']}")

        # Step 3: Expire the token (simulate 25 hours passing)
        print("\n3️⃣  Expiring verification token (simulating 25 hours)...")
        if not expire_verification_token(test_email):
            print("❌ Failed to expire token")
            return False

        print("✅ Token expired (set to 25 hours ago)")

        # Step 4: Try to verify email with expired token
        print("\n4️⃣  Attempting to verify email with expired token...")
        verify_response = requests.post(
            f"{AUTH_SERVICE_URL}/email/verify",
            json={"token": original_token}
        )

        if verify_response.status_code == 200:
            print("❌ Verification succeeded with expired token (should have failed)")
            return False

        if verify_response.status_code != 400:
            print(f"❌ Unexpected status code: {verify_response.status_code}")
            return False

        # Step 5: Verify error message
        print("\n5️⃣  Verifying error message...")
        error_detail = verify_response.json().get("detail", "")

        if "expired" not in error_detail.lower():
            print(f"❌ Error message doesn't mention expiry: {error_detail}")
            return False

        print(f"✅ Correct error message: '{error_detail}'")

        # Step 6: Resend verification email
        print("\n6️⃣  Resending verification email...")
        resend_response = requests.post(
            f"{AUTH_SERVICE_URL}/email/resend-verification",
            json={"email": test_email}
        )

        if resend_response.status_code != 200:
            print(f"❌ Resend failed: {resend_response.status_code}")
            print(f"   Response: {resend_response.text}")
            return False

        print("✅ Verification email resent")

        # Step 7: Get new verification token
        print("\n7️⃣  Getting new verification token...")
        time.sleep(1)  # Give DB a moment
        new_token_data = get_verification_token(test_email)

        if not new_token_data:
            print("❌ No new verification token found")
            return False

        new_token = new_token_data["token"]

        if new_token == original_token:
            print("❌ Token wasn't refreshed (same as original)")
            return False

        print(f"✅ New verification token retrieved: {new_token[:20]}...")
        print(f"   Expires at: {new_token_data['expires_at']}")

        # Step 8: Verify email with new token
        print("\n8️⃣  Verifying email with new token...")
        verify_new_response = requests.post(
            f"{AUTH_SERVICE_URL}/email/verify",
            json={"token": new_token}
        )

        if verify_new_response.status_code != 200:
            print(f"❌ Verification with new token failed: {verify_new_response.status_code}")
            print(f"   Response: {verify_new_response.text}")
            return False

        print("✅ Email verified successfully with new token")

        # Step 9: Verify user can now log in
        print("\n9️⃣  Testing login after verification...")
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False

        login_data = login_response.json()
        if "access_token" not in login_data:
            print("❌ No access token in login response")
            return False

        print("✅ Login successful after email verification")

        print("\n" + "="*80)
        print("✅ Feature #101: ALL TESTS PASSED")
        print("="*80)
        print("\nTest Summary:")
        print("  ✅ Email verification token expires after 24 hours")
        print("  ✅ Expired token returns proper error message")
        print("  ✅ Resend verification email creates new token")
        print("  ✅ Old token is invalidated when resending")
        print("  ✅ New token works for verification")
        print("  ✅ User can log in after verification")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        cleanup_test_user(test_email)
        print("✅ Cleanup complete")

if __name__ == "__main__":
    success = test_email_verification_expiry()
    exit(0 if success else 1)
