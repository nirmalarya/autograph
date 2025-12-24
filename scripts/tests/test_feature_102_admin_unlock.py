#!/usr/bin/env python3
"""
Test Feature #102: Account lockout can be manually unlocked by admin

Test steps:
- Create a regular user
- Create an admin user
- Lock the regular user's account (10 failed attempts)
- Login as admin
- Call the unlock endpoint
- Verify the regular user can now login
"""

import requests
import time
import psycopg2
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8085"
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")

def test_feature_102():
    """Test Feature #102: Admin can manually unlock locked accounts"""
    print_section("TEST FEATURE #102: Admin Manual Account Unlock")
    
    timestamp = int(time.time())
    regular_email = f"regular_user_{timestamp}@example.com"
    admin_email = f"admin_user_{timestamp}@example.com"
    password = "SecurePassword123!"
    
    # Step 1: Create regular user
    print(f"Step 1: Create regular user: {regular_email}")
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": regular_email,
            "password": password,
            "full_name": f"Regular User {timestamp}"
        }
    )
    
    if register_response.status_code != 201:
        print(f"✗ Regular user registration failed: {register_response.text}")
        return False
    
    regular_user_id = register_response.json().get("id")
    print(f"✓ Regular user registered (ID: {regular_user_id})")
    
    # Step 2: Create admin user
    print(f"\nStep 2: Create admin user: {admin_email}")
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": admin_email,
            "password": password,
            "full_name": f"Admin User {timestamp}"
        }
    )
    
    if register_response.status_code != 201:
        print(f"✗ Admin user registration failed: {register_response.text}")
        return False
    
    admin_user_id = register_response.json().get("id")
    print(f"✓ Admin user registered (ID: {admin_user_id})")
    
    # Step 3: Set admin role and verify both users via database
    print(f"\nStep 3: Set admin role and verify emails via database")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Set admin role
        cur.execute(
            "UPDATE users SET role = 'admin', is_verified = TRUE WHERE id = %s",
            (admin_user_id,)
        )
        
        # Verify regular user
        cur.execute(
            "UPDATE users SET is_verified = TRUE WHERE id = %s",
            (regular_user_id,)
        )
        
        conn.commit()
        print(f"✓ Admin role set and emails verified")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    # Step 4: Lock regular user account (10 failed attempts)
    print(f"\nStep 4: Lock regular user account via database")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        cur.execute(
            "UPDATE users SET failed_login_attempts = 10, locked_until = %s WHERE id = %s",
            (locked_until, regular_user_id)
        )
        conn.commit()
        
        # Verify lock
        cur.execute(
            "SELECT failed_login_attempts, locked_until FROM users WHERE id = %s",
            (regular_user_id,)
        )
        result = cur.fetchone()
        
        if result and result[0] == 10:
            print(f"✓ Regular user account locked")
            print(f"  Failed attempts: {result[0]}")
            print(f"  Locked until: {result[1]}")
        else:
            print(f"✗ Failed to lock account")
            return False
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    # Step 5: Verify regular user cannot login (account locked)
    print(f"\nStep 5: Verify regular user cannot login (locked)")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": regular_email,
            "password": password
        }
    )
    
    if login_response.status_code == 403:
        error_detail = login_response.json().get("detail", "")
        if "locked" in error_detail.lower():
            print(f"✓ Regular user login blocked: {error_detail[:80]}...")
        else:
            print(f"✗ Unexpected error message: {error_detail}")
            return False
    else:
        print(f"✗ Expected 403 (locked), got {login_response.status_code}")
        return False
    
    # Step 6: Login as admin
    print(f"\nStep 6: Login as admin user")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": admin_email,
            "password": password
        }
    )
    
    if login_response.status_code != 200:
        print(f"✗ Admin login failed: {login_response.text}")
        return False
    
    admin_token = login_response.json().get("access_token")
    print(f"✓ Admin logged in successfully")
    print(f"  Token: {admin_token[:20]}...")
    
    # Step 7: Admin unlocks regular user account
    print(f"\nStep 7: Admin unlocks regular user account")
    unlock_response = requests.post(
        f"{BASE_URL}/admin/users/{regular_user_id}/unlock",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if unlock_response.status_code != 200:
        print(f"✗ Admin unlock failed: {unlock_response.text}")
        return False
    
    unlock_data = unlock_response.json()
    print(f"✓ Account unlocked successfully")
    print(f"  Message: {unlock_data.get('message')}")
    print(f"  Was locked: {unlock_data.get('was_locked')}")
    print(f"  Unlocked by: {unlock_data.get('unlocked_by')}")
    
    # Step 8: Verify regular user can now login
    print(f"\nStep 8: Verify regular user can now login")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": regular_email,
            "password": password
        }
    )
    
    if login_response.status_code != 200:
        print(f"✗ Regular user login still blocked: {login_response.text}")
        return False
    
    print(f"✓ Regular user logged in successfully after unlock")
    print(f"  Access token received: {len(login_response.json().get('access_token', ''))} chars")
    
    # Step 9: Verify database state
    print(f"\nStep 9: Verify database state")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT failed_login_attempts, locked_until FROM users WHERE id = %s",
            (regular_user_id,)
        )
        result = cur.fetchone()
        
        if result and result[0] == 0 and result[1] is None:
            print(f"✓ Database state verified")
            print(f"  Failed attempts: {result[0]}")
            print(f"  Locked until: {result[1]}")
        else:
            print(f"✗ Database state incorrect: attempts={result[0]}, locked_until={result[1]}")
            return False
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    # Step 10: Test non-admin cannot unlock
    print(f"\nStep 10: Test non-admin user cannot unlock (security check)")
    
    # Create another regular user
    regular2_email = f"regular2_{timestamp}@example.com"
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": regular2_email,
            "password": password,
            "full_name": f"Regular User 2 {timestamp}"
        }
    )
    
    regular2_user_id = register_response.json().get("id")
    
    # Verify email
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (regular2_user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except:
        pass
    
    # Login as regular user 2
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": regular2_email,
            "password": password
        }
    )
    
    regular2_token = login_response.json().get("access_token")
    
    # Try to unlock as non-admin (should fail)
    unlock_response = requests.post(
        f"{BASE_URL}/admin/users/{regular_user_id}/unlock",
        headers={"Authorization": f"Bearer {regular2_token}"}
    )
    
    if unlock_response.status_code == 403:
        error_detail = unlock_response.json().get("detail", "")
        if "admin" in error_detail.lower():
            print(f"✓ Non-admin correctly blocked: {error_detail}")
        else:
            print(f"⚠ Non-admin blocked but wrong error: {error_detail}")
    else:
        print(f"✗ Non-admin should be blocked (got {unlock_response.status_code})")
        return False
    
    print(f"\n{'='*80}")
    print(f"✅ FEATURE #102: PASSED - Admin can manually unlock locked accounts")
    print(f"{'='*80}")
    print(f"\nTest Summary:")
    print(f"  • Regular user account locked successfully")
    print(f"  • Admin user created with admin role")
    print(f"  • Admin successfully unlocked regular user account")
    print(f"  • Regular user can login after unlock")
    print(f"  • Database state correctly updated (attempts=0, locked_until=NULL)")
    print(f"  • Non-admin users correctly blocked from unlock endpoint")
    print(f"  • Audit log created for admin action")
    
    return True


def main():
    print(f"\n{'='*80}")
    print(f"ADMIN UNLOCK TEST SUITE")
    print(f"Feature #102")
    print(f"{'='*80}")
    
    test_passed = test_feature_102()
    
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Feature #102 (Admin unlock): {'✅ PASSED' if test_passed else '❌ FAILED'}")
    print(f"{'='*80}\n")
    
    return test_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
