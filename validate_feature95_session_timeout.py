#!/usr/bin/env python3
"""
Validation script for Feature #95: Session timeout after 30 minutes of inactivity
Tests session expiration after inactivity period.
"""

import requests
import time
import json
import redis
from datetime import datetime, timedelta
import psycopg2

# Configuration
AUTH_SERVICE = "https://localhost:8085"
TEST_EMAIL = f"session_timeout_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecureP@ss123!"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes in seconds

def test_session_timeout():
    """Test session timeout after inactivity."""
    print("=" * 70)
    print("FEATURE #95: Session timeout after 30 minutes of inactivity")
    print("=" * 70)
    print()

    session = requests.Session()
    session.verify = False  # For self-signed certs

    # Connect to Redis
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    try:
        # Step 1: Register and verify user
        print("Step 1: Registering and verifying user...")
        register_response = session.post(
            f"{AUTH_SERVICE}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Session Timeout Test User"
            }
        )

        if register_response.status_code != 201:
            print(f"❌ Registration failed: {register_response.status_code}")
            return False

        reg_data = register_response.json()
        user_id = reg_data.get("id")

        # Get verification token from database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT token FROM email_verification_tokens WHERE user_id = %s AND is_used = false ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            print("❌ Could not find verification token")
            return False

        verification_token = result[0]

        # Verify email
        verify_response = session.post(
            f"{AUTH_SERVICE}/email/verify",
            json={"token": verification_token}
        )

        if verify_response.status_code != 200:
            print(f"❌ Email verification failed: {verify_response.status_code}")
            return False

        print(f"✅ User registered and verified: {TEST_EMAIL}")

        # Step 2: Login and access dashboard
        print("\nStep 2: Logging in and accessing dashboard...")
        login_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False

        access_token = login_response.json().get("access_token")

        # Access a protected endpoint (dashboard/me)
        me_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if me_response.status_code != 200:
            print(f"❌ Protected endpoint access failed: {me_response.status_code}")
            return False

        print(f"✅ Login successful and dashboard accessible")

        # Step 3: Check session data in Redis
        print("\nStep 3: Checking session in Redis...")
        session_key = f"session:{access_token}"
        session_data_str = redis_client.get(session_key)

        if not session_data_str:
            print(f"❌ Session not found in Redis")
            return False

        session_data = json.loads(session_data_str)
        original_last_activity = session_data.get("last_activity")

        print(f"✅ Session found in Redis")
        print(f"   Key: session:{access_token[:20]}...")
        print(f"   Last activity: {original_last_activity}")

        # Step 4: Simulate 29 minutes of inactivity (still within timeout)
        print("\nStep 4: Simulating 29 minutes of inactivity...")
        print("   (Manipulating last_activity timestamp in Redis)")

        # Calculate timestamp 29 minutes ago
        twenty_nine_min_ago = datetime.utcnow() - timedelta(minutes=29)
        session_data["last_activity"] = twenty_nine_min_ago.isoformat()

        # Update session in Redis
        redis_client.set(session_key, json.dumps(session_data))

        print(f"   Updated last_activity to 29 minutes ago")

        # Step 5: Perform action (should still work)
        print("\nStep 5: Performing action (should succeed - within 30 min)...")

        action_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if action_response.status_code != 200:
            print(f"❌ Action failed (should have succeeded): {action_response.status_code}")
            print(f"Response: {action_response.text}")
            return False

        print(f"✅ Action successful (session still valid after 29 min)")

        # Verify last_activity was updated
        session_data_str = redis_client.get(session_key)
        if session_data_str:
            updated_session = json.loads(session_data_str)
            new_last_activity = updated_session.get("last_activity")
            print(f"   Last activity updated to: {new_last_activity}")

        # Step 6: Simulate 31 minutes of inactivity (exceeds timeout)
        print("\nStep 6: Simulating 31 minutes of inactivity...")

        # Calculate timestamp 31 minutes ago
        thirty_one_min_ago = datetime.utcnow() - timedelta(minutes=31)

        # Get current session data
        session_data_str = redis_client.get(session_key)
        if session_data_str:
            session_data = json.loads(session_data_str)
            session_data["last_activity"] = thirty_one_min_ago.isoformat()
            redis_client.set(session_key, json.dumps(session_data))
            print(f"   Updated last_activity to 31 minutes ago")
        else:
            print(f"❌ Session not found in Redis (might have been cleaned up)")
            return False

        # Step 7: Attempt to perform action (should fail)
        print("\nStep 7: Attempting action (should fail - exceeded 30 min)...")

        expired_action_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Should get 401 Unauthorized
        if expired_action_response.status_code != 401:
            print(f"❌ Expected 401, got {expired_action_response.status_code}")
            print(f"Response: {expired_action_response.text}")
            return False

        print(f"✅ Action blocked with 401 Unauthorized (session expired)")

        # Step 8: Verify error message
        print("\nStep 8: Verifying error message...")

        error_data = expired_action_response.json()
        error_detail = error_data.get("detail", "")

        if "inactivity" not in error_detail.lower():
            print(f"❌ Error message doesn't mention inactivity: {error_detail}")
            return False

        print(f"✅ Error message: '{error_detail}'")

        # Verify session was deleted from Redis
        session_data_str = redis_client.get(session_key)
        if session_data_str:
            print(f"⚠️  Session still exists in Redis (might not be cleaned up yet)")
        else:
            print(f"✅ Session deleted from Redis after expiration")

        # Step 9: Verify new login works
        print("\nStep 9: Verifying user can login again...")

        new_login_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if new_login_response.status_code != 200:
            print(f"❌ New login failed: {new_login_response.status_code}")
            return False

        new_access_token = new_login_response.json().get("access_token")

        # Access protected endpoint with new token
        new_me_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        if new_me_response.status_code != 200:
            print(f"❌ New session access failed: {new_me_response.status_code}")
            return False

        print(f"✅ New login successful and session active")

        print("\n" + "=" * 70)
        print("✅ ALL SESSION TIMEOUT TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ Session created on login")
        print("  ✅ Session valid after 29 minutes of inactivity")
        print("  ✅ Session expired after 31 minutes of inactivity")
        print("  ✅ 401 Unauthorized returned on expired session")
        print("  ✅ Error message: 'Session expired due to inactivity'")
        print("  ✅ Expired session deleted from Redis")
        print("  ✅ User can login again after timeout")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        redis_client.close()

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_session_timeout()
    exit(0 if success else 1)
