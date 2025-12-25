#!/usr/bin/env python3
"""
Feature #103: Account lockout can be manually unlocked by admin

This test validates that an admin user can manually unlock a locked user account.

Test flow:
1. Register and verify a regular test user
2. Register and verify an admin test user
3. Lock the regular user's account (10 failed login attempts)
4. Admin logs in
5. Admin unlocks the user's account via /admin/users/{user_id}/unlock
6. Verify the account is unlocked
7. User successfully logs in with correct password
"""

import requests
import sys
import time
from datetime import datetime, timezone
import redis

BASE_URL = "http://localhost:8085"
VERIFY_SSL = False

def print_step(step_num, description):
    """Print a test step."""
    print(f"\n{'='*80}")
    print(f"Step {step_num}: {description}")
    print('='*80)

def clear_all_redis():
    """Clear ALL Redis keys to reset rate limiting completely."""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.flushall()
        print("✅ Cleared all Redis keys")
        return True
    except Exception as e:
        print(f"⚠️  Could not clear Redis: {e}")
        return False

def lock_user_account_directly(user_id):
    """Directly lock user account in database (simulating 10 failed attempts)."""
    import psycopg2
    from datetime import timedelta
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
    cur.execute(
        "UPDATE users SET failed_login_attempts = 10, locked_until = %s WHERE id = %s",
        (locked_until, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return locked_until

def register_user(email, password, full_name):
    """Register a new user."""
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        },
        verify=VERIFY_SSL
    )
    return response

def verify_email(user_id):
    """Mark user as verified (simulate email verification)."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def promote_to_admin(user_id):
    """Promote user to admin role."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 'admin' WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def login(email, password):
    """Login a user."""
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        },
        verify=VERIFY_SSL
    )
    return response

def check_user_lockout_status(user_id):
    """Check if user is locked out."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT locked_until, failed_login_attempts FROM users WHERE id = %s",
        (user_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        locked_until, failed_attempts = result
        is_locked = locked_until is not None and locked_until > datetime.now(timezone.utc)
        return {
            "is_locked": is_locked,
            "locked_until": locked_until,
            "failed_attempts": failed_attempts
        }
    return None

def admin_unlock_user(admin_token, user_id):
    """Admin unlocks a user account."""
    response = requests.post(
        f"{BASE_URL}/admin/users/{user_id}/unlock",
        headers={"Authorization": f"Bearer {admin_token}"},
        verify=VERIFY_SSL
    )
    return response

def main():
    """Run the validation test."""
    print("\n" + "="*80)
    print("Feature #103: Account lockout can be manually unlocked by admin")
    print("="*80)

    # Generate unique emails
    timestamp = int(time.time())
    regular_email = f"test_user_{timestamp}@example.com"
    admin_email = f"test_admin_{timestamp}@example.com"
    password = "SecurePassword123!"
    wrong_password = "WrongPassword456!"

    try:
        # Step 1: Register regular user
        print_step(1, "Register regular test user")
        response = register_user(regular_email, password, "Test User")
        if response.status_code != 201:
            print(f"❌ Failed to register user: {response.status_code} - {response.text}")
            return False

        user_data = response.json()
        user_id = user_data["id"]
        print(f"✅ User registered: {regular_email} (ID: {user_id})")

        # Verify the user
        verify_email(user_id)
        print(f"✅ User verified")

        # Step 2: Register admin user
        print_step(2, "Register admin test user")
        response = register_user(admin_email, password, "Test Admin")
        if response.status_code != 201:
            print(f"❌ Failed to register admin: {response.status_code} - {response.text}")
            return False

        admin_data = response.json()
        admin_id = admin_data["id"]
        print(f"✅ Admin registered: {admin_email} (ID: {admin_id})")

        # Verify and promote to admin
        verify_email(admin_id)
        promote_to_admin(admin_id)
        print(f"✅ Admin verified and promoted to admin role")

        # Step 3: Lock the regular user's account
        print_step(3, "Lock user account (simulate 10 failed login attempts)")

        # Clear all Redis to avoid any rate limiting interference
        clear_all_redis()

        # Directly set account to locked state (simulating 10 failed attempts)
        locked_until = lock_user_account_directly(user_id)
        print(f"✅ Account locked directly in database until: {locked_until}")

        # Verify account is locked
        lockout_status = check_user_lockout_status(user_id)
        if not lockout_status or not lockout_status["is_locked"]:
            print(f"❌ Account should be locked but is not")
            print(f"   Lockout status: {lockout_status}")
            return False

        print(f"✅ Account locked until: {lockout_status['locked_until']}")
        print(f"   Failed attempts: {lockout_status['failed_attempts']}")

        # Verify login fails even with correct password
        clear_all_redis()
        response = login(regular_email, password)
        if response.status_code != 403:
            print(f"❌ Expected 403 Forbidden, got {response.status_code}")
            return False

        error_data = response.json()
        if "locked" not in error_data.get("detail", "").lower():
            print(f"❌ Error message should mention 'locked': {error_data.get('detail')}")
            return False

        print(f"✅ Login correctly blocked: {error_data['detail']}")

        # Step 4: Admin logs in
        print_step(4, "Admin logs in")
        response = login(admin_email, password)
        if response.status_code != 200:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return False

        admin_token = response.json()["access_token"]
        print(f"✅ Admin logged in successfully")

        # Step 5: Admin unlocks user account
        print_step(5, "Admin unlocks user account")
        response = admin_unlock_user(admin_token, user_id)
        if response.status_code != 200:
            print(f"❌ Admin unlock failed: {response.status_code} - {response.text}")
            return False

        unlock_data = response.json()
        print(f"✅ Account unlocked successfully")
        print(f"   Message: {unlock_data.get('message')}")
        print(f"   Unlocked by: {unlock_data.get('unlocked_by')}")
        print(f"   Was locked: {unlock_data.get('was_locked')}")

        if not unlock_data.get('was_locked'):
            print(f"❌ Expected was_locked to be True")
            return False

        # Step 6: Verify account is unlocked
        print_step(6, "Verify account is unlocked in database")
        lockout_status = check_user_lockout_status(user_id)
        if lockout_status["is_locked"]:
            print(f"❌ Account should be unlocked but is still locked")
            print(f"   Lockout status: {lockout_status}")
            return False

        if lockout_status["failed_attempts"] != 0:
            print(f"❌ Failed attempts should be reset to 0, got {lockout_status['failed_attempts']}")
            return False

        print(f"✅ Account unlocked in database")
        print(f"   Locked until: {lockout_status['locked_until']}")
        print(f"   Failed attempts: {lockout_status['failed_attempts']}")

        # Step 7: User successfully logs in
        print_step(7, "User successfully logs in with correct password")
        clear_all_redis()
        response = login(regular_email, password)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False

        print(f"✅ User logged in successfully after admin unlock")

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED - Feature #103 is working correctly!")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
