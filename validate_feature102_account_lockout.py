#!/usr/bin/env python3
"""
Feature #102 Validation: Account lockout after 10 failed login attempts

Steps:
1. Attempt login with wrong password 10 times
2. Verify account locked
3. Attempt login with correct password
4. Verify error: 'Account locked due to too many failed attempts'
5. Verify lockout duration: 1 hour
6. Wait 1 hour (or manipulate locked_until)
7. Verify account automatically unlocked
8. Login with correct password
9. Verify login succeeds
"""

import requests
import psycopg2
import os
import time
import secrets
import redis
from datetime import datetime, timedelta, timezone

# Test configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8085")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "autograph")
POSTGRES_USER = os.getenv("POSTGRES_USER", "autograph")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

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

def verify_user(email: str):
    """Verify user's email to allow login."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE users SET is_verified = true WHERE email = %s", (email,))

    conn.commit()
    cur.close()
    conn.close()

def get_user_lockout_info(email: str):
    """Get user's lockout information from database."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT failed_login_attempts, locked_until
        FROM users
        WHERE email = %s
    """, (email,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return {
            "failed_attempts": row[0],
            "locked_until": row[1]
        }
    return None

def clear_lockout(email: str):
    """Clear lockout by setting locked_until to past time."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Set locked_until to 2 hours ago (past the lockout period)
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    cur.execute("""
        UPDATE users
        SET locked_until = %s
        WHERE email = %s
    """, (past_time, email))

    conn.commit()
    cur.close()
    conn.close()

def clear_ip_rate_limit():
    """Clear IP rate limit in Redis to allow testing account lockout."""
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        # Clear all rate limit keys for localhost
        keys = redis_client.keys("rate_limit:login:*")
        if keys:
            redis_client.delete(*keys)
        redis_client.close()
    except Exception as e:
        print(f"Warning: Could not clear Redis rate limit: {e}")

def test_account_lockout():
    """Test account lockout after 10 failed login attempts."""
    print("\n" + "="*80)
    print("Feature #102: Account lockout after 10 failed login attempts")
    print("="*80)

    # Generate unique test email
    test_email = f"test_lockout_{secrets.token_hex(4)}@example.com"
    test_password = "SecurePassword123!"
    wrong_password = "WrongPassword456!"

    try:
        # Clean up any existing test user
        cleanup_test_user(test_email)

        # Step 0: Register and verify user
        print("\n0️⃣  Setting up test user...")
        register_response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test User Lockout"
            }
        )

        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.status_code}")
            return False

        # Verify email to allow login
        verify_user(test_email)
        print(f"✅ Test user created and verified: {test_email}")

        # Step 1: Attempt login with wrong password 10 times
        print("\n1️⃣  Attempting login with wrong password 10 times...")
        print("   (Clearing IP rate limit to isolate account lockout testing)")

        for i in range(10):
            # Clear IP rate limit every 4 attempts to avoid IP-based blocking
            # This allows us to test the account lockout mechanism (10 attempts)
            # independently of the IP rate limit (5 attempts)
            if i % 4 == 0:
                clear_ip_rate_limit()

            login_response = requests.post(
                f"{AUTH_SERVICE_URL}/login",
                json={
                    "email": test_email,
                    "password": wrong_password
                }
            )

            # First 9 attempts should return 401 (unauthorized)
            if i < 9:
                if login_response.status_code != 401:
                    print(f"❌ Unexpected status code on attempt {i+1}: {login_response.status_code}")
                    print(f"   Response: {login_response.text}")
                    return False
                print(f"   Attempt {i+1}/10: Failed (expected) ✓")
            else:
                # 10th attempt should trigger lockout (403)
                if login_response.status_code != 403:
                    print(f"❌ Expected 403 on attempt {i+1}, got: {login_response.status_code}")
                    print(f"   Response: {login_response.text}")
                    return False
                print(f"   Attempt {i+1}/10: Account locked (expected) ✓")

        print("✅ Account locked after 10 failed attempts")

        # Step 2: Verify account locked in database
        print("\n2️⃣  Verifying account lockout in database...")
        lockout_info = get_user_lockout_info(test_email)

        if not lockout_info:
            print("❌ User not found in database")
            return False

        if lockout_info["failed_attempts"] != 10:
            print(f"❌ Expected 10 failed attempts, got: {lockout_info['failed_attempts']}")
            return False

        if not lockout_info["locked_until"]:
            print("❌ locked_until not set")
            return False

        print(f"✅ Failed attempts: {lockout_info['failed_attempts']}")
        print(f"✅ Locked until: {lockout_info['locked_until']}")

        # Step 3: Attempt login with correct password (should still fail)
        print("\n3️⃣  Attempting login with correct password while locked...")
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        if login_response.status_code != 403:
            print(f"❌ Expected 403 (account locked), got: {login_response.status_code}")
            return False

        # Step 4: Verify error message
        print("\n4️⃣  Verifying error message...")
        error_detail = login_response.json().get("detail", "")

        if "locked" not in error_detail.lower():
            print(f"❌ Error message doesn't mention lockout: {error_detail}")
            return False

        print(f"✅ Correct error message: '{error_detail}'")

        # Step 5: Verify lockout duration is 1 hour
        print("\n5️⃣  Verifying lockout duration...")
        locked_until = lockout_info["locked_until"]
        now = datetime.now(timezone.utc)

        # Calculate time difference (should be close to 1 hour)
        time_diff = (locked_until - now).total_seconds() / 3600  # Convert to hours

        # Allow 5 minute tolerance (59-61 minutes)
        if not (0.95 <= time_diff <= 1.05):
            print(f"❌ Lockout duration not ~1 hour: {time_diff:.2f} hours")
            return False

        print(f"✅ Lockout duration: {time_diff:.2f} hours (~1 hour)")

        # Step 6: Simulate waiting 1 hour by clearing lockout
        print("\n6️⃣  Simulating 1 hour wait (clearing lockout)...")
        clear_lockout(test_email)
        print("✅ Lockout time set to past (simulating 1 hour wait)")

        # Step 7: Verify account automatically unlocked
        print("\n7️⃣  Verifying account automatically unlocked...")
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login after lockout expired failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False

        # Step 8: Verify login succeeds
        print("\n8️⃣  Verifying successful login...")
        login_data = login_response.json()

        if "access_token" not in login_data:
            print("❌ No access token in login response")
            return False

        print("✅ Login successful after lockout expired")

        # Step 9: Verify failed attempts reset
        print("\n9️⃣  Verifying failed attempts counter reset...")
        lockout_info = get_user_lockout_info(test_email)

        if lockout_info["failed_attempts"] != 0:
            print(f"❌ Failed attempts not reset: {lockout_info['failed_attempts']}")
            return False

        if lockout_info["locked_until"] is not None:
            print(f"❌ locked_until not cleared: {lockout_info['locked_until']}")
            return False

        print("✅ Failed attempts counter reset to 0")
        print("✅ locked_until cleared")

        print("\n" + "="*80)
        print("✅ Feature #102: ALL TESTS PASSED")
        print("="*80)
        print("\nTest Summary:")
        print("  ✅ Account locks after 10 failed login attempts")
        print("  ✅ Locked account cannot login even with correct password")
        print("  ✅ Proper error message shown when account is locked")
        print("  ✅ Lockout duration is 1 hour")
        print("  ✅ Account automatically unlocks after 1 hour")
        print("  ✅ User can login after lockout expires")
        print("  ✅ Failed attempts counter resets after successful login")

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
    success = test_account_lockout()
    exit(0 if success else 1)
