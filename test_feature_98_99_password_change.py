"""
Features #98-99: Password Change with Session Invalidation

Test verifies:
1. Password change requires current password (#98)
2. Wrong current password is rejected (#98)
3. Password change invalidates all sessions (#99)
4. User must login again after password change (#99)
"""

import requests
import time
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"

def print_separator(title=""):
    """Print a separator line."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print('=' * 80)
    else:
        print('=' * 80)

def register_user(email: str, password: str, role: str = "viewer"):
    """Register a new user."""
    url = f"{AUTH_SERVICE_URL}/register"
    data = {
        "email": email,
        "password": password,
        "role": role
    }
    response = requests.post(url, json=data)
    return response

def login_user(email: str, password: str):
    """Login and return access token."""
    url = f"{AUTH_SERVICE_URL}/login"
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def verify_email(user_id: str):
    """Verify email directly in database for testing."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def change_password(token: str, current_password: str, new_password: str):
    """Change password."""
    url = f"{AUTH_SERVICE_URL}/password/change"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "current_password": current_password,
        "new_password": new_password
    }
    response = requests.post(url, json=data, headers=headers)
    return response

def test_protected_endpoint(token: str):
    """Test accessing a protected endpoint."""
    url = f"{AUTH_SERVICE_URL}/permissions/viewer"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response

def main():
    """Run Features #98-99 tests."""
    
    print_separator("FEATURES #98-99: PASSWORD CHANGE TEST SUITE")
    print(f"Testing against: {AUTH_SERVICE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate unique email address
    timestamp = int(time.time())
    email = f"pwtest_{timestamp}@example.com"
    password = "TestPassword123!"
    new_password = "NewPassword456!"
    
    print_separator("TEST FEATURES #98-99: Password Change")
    
    # Step 1: Register user
    print("\nStep 1: Register user")
    response = register_user(email, password, "viewer")
    if response.status_code == 201:
        user_data = response.json()
        user_id = user_data["id"]
        print(f"✓ User registered (ID: {user_id})")
        print(f"  Email: {email}")
        
        # Verify email
        verify_email(user_id)
        print("✓ Email verified via database")
    else:
        print(f"✗ Failed to register user: {response.status_code} - {response.text}")
        return False
    
    # Step 2: Login from device 1
    print("\nStep 2: Login from device 1")
    token1 = login_user(email, password)
    if token1:
        print(f"✓ Device 1 logged in successfully")
        print(f"  Token: {token1[:50]}...")
    else:
        print("✗ Device 1 login failed")
        return False
    
    # Step 3: Login from device 2
    print("\nStep 3: Login from device 2 (simulating multiple sessions)")
    token2 = login_user(email, password)
    if token2:
        print(f"✓ Device 2 logged in successfully")
        print(f"  Token: {token2[:50]}...")
    else:
        print("✗ Device 2 login failed")
        return False
    
    # Step 4: Verify both devices can access protected endpoints
    print("\nStep 4: Verify both devices have valid sessions")
    response1 = test_protected_endpoint(token1)
    if response1.status_code == 200:
        print("✓ Device 1 can access protected endpoint")
    else:
        print(f"✗ Device 1 cannot access endpoint: {response1.status_code}")
        return False
    
    response2 = test_protected_endpoint(token2)
    if response2.status_code == 200:
        print("✓ Device 2 can access protected endpoint")
    else:
        print(f"✗ Device 2 cannot access endpoint: {response2.status_code}")
        return False
    
    # Step 5: Try to change password without current password (Feature #98)
    print("\nStep 5: Feature #98 - Try to change password without correct current password")
    response = change_password(token1, "WrongPassword123!", new_password)
    if response.status_code == 400:
        error_detail = response.json()["detail"]
        print(f"✓ Password change correctly rejected with wrong current password")
        print(f"  Error: {error_detail}")
    else:
        print(f"✗ Password change should have been rejected: {response.status_code}")
        return False
    
    # Step 6: Change password with correct current password (Feature #98)
    print("\nStep 6: Feature #98 - Change password with correct current password")
    response = change_password(token1, password, new_password)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Password changed successfully")
        print(f"  Message: {result['message']}")
        print(f"  Detail: {result['detail']}")
        print(f"  Sessions invalidated: {result['sessions_invalidated']}")
    else:
        print(f"✗ Password change failed: {response.status_code} - {response.text}")
        return False
    
    # Step 7: Verify device 1 is logged out (Feature #99)
    print("\nStep 7: Feature #99 - Verify device 1 is logged out")
    response1 = test_protected_endpoint(token1)
    if response1.status_code == 401:
        print("✓ Device 1 correctly logged out (401 Unauthorized)")
        error_detail = response1.json()["detail"]
        print(f"  Error: {error_detail}")
    else:
        print(f"✗ Device 1 should be logged out: {response1.status_code}")
        return False
    
    # Step 8: Verify device 2 is also logged out (Feature #99)
    print("\nStep 8: Feature #99 - Verify device 2 is also logged out")
    response2 = test_protected_endpoint(token2)
    if response2.status_code == 401:
        print("✓ Device 2 correctly logged out (401 Unauthorized)")
        error_detail = response2.json()["detail"]
        print(f"  Error: {error_detail}")
    else:
        print(f"✗ Device 2 should be logged out: {response2.status_code}")
        return False
    
    # Step 9: Verify old password doesn't work
    print("\nStep 9: Verify old password doesn't work")
    token_old = login_user(email, password)
    if token_old is None:
        print("✓ Old password correctly rejected")
    else:
        print("✗ Old password should not work")
        return False
    
    # Wait for blacklist to expire (2 seconds TTL + 1 second buffer)
    print("\nWaiting 3 seconds for blacklist to expire...")
    time.sleep(3)
    
    # Step 10: Verify new password works
    print("\nStep 10: Verify user can login with new password")
    token_new = login_user(email, new_password)
    if token_new:
        print(f"✓ Login successful with new password")
        print(f"  New token: {token_new[:50]}...")
    else:
        print("✗ Login with new password failed")
        return False
    
    # Step 11: Verify new token works
    print("\nStep 11: Verify new session works")
    response_new = test_protected_endpoint(token_new)
    if response_new.status_code == 200:
        print("✓ New session can access protected endpoint")
    else:
        print(f"✗ New session cannot access endpoint: {response_new.status_code}")
        return False
    
    # Summary
    print_separator("✅ FEATURES #98-99: PASSED - Password change working correctly")
    
    print("\nTest Summary:")
    print("  Feature #98: Password change requires current password")
    print("    • Wrong current password correctly rejected ✅")
    print("    • Correct current password accepted ✅")
    print("    • Password successfully changed ✅")
    print()
    print("  Feature #99: Password change invalidates all sessions")
    print("    • Device 1 session invalidated ✅")
    print("    • Device 2 session invalidated ✅")
    print("    • Old password no longer works ✅")
    print("    • New password works correctly ✅")
    print("    • New session fully functional ✅")
    
    print_separator("TEST SUMMARY")
    print("Features #98-99 (Password change): ✅ PASSED")
    print_separator()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
