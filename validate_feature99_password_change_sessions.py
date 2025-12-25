#!/usr/bin/env python3
"""
Feature #99 Validation: Password change invalidates all existing sessions except current

Test Plan:
1. Login from device 1
2. Login from device 2
3. From device 1, change password
4. Verify device 1 still logged in (can access protected endpoint)
5. From device 2, attempt to access protected endpoint
6. Verify 401 Unauthorized response
7. Verify device 2 logged out
8. Verify message about password changed
"""

import requests
import sys
import time
from datetime import datetime

# Base URLs
AUTH_URL = "http://localhost:8080/api/auth"
BASE_URL = "http://localhost:8080/api"

def print_step(step_num, description):
    """Print test step."""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print('='*80)

def print_result(success, message):
    """Print test result."""
    symbol = "✅" if success else "❌"
    print(f"{symbol} {message}")
    return success

def register_unique_user():
    """Register a unique test user."""
    timestamp = int(time.time() * 1000)
    email = f"test_feature99_{timestamp}@example.com"
    password = "TestPassword123!@#"

    payload = {
        "email": email,
        "password": password,
        "full_name": "Feature 99 Test User"
    }

    response = requests.post(f"{AUTH_URL}/register", json=payload)

    if response.status_code == 201:
        print(f"✅ User registered: {email}")
        # Verify email automatically
        verify_email(email)
        return email, password
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None

def verify_email(email):
    """Verify email by setting is_verified to true in database."""
    import psycopg2

    # Connect to database to verify email
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        cursor = conn.cursor()

        # Set is_verified to true for this email
        cursor.execute(
            "UPDATE users SET is_verified = true WHERE email = %s",
            (email,)
        )
        conn.commit()

        print(f"✅ Email verified (is_verified set to true)")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not verify email automatically: {e}")
        print("   Continuing anyway...")

def login(email, password, device_name=""):
    """Login and return access token."""
    payload = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{AUTH_URL}/login", json=payload)

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ Login successful{' (' + device_name + ')' if device_name else ''}")
        return token
    else:
        print(f"❌ Login failed{' (' + device_name + ')' if device_name else ''}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def change_password(token, current_password, new_password):
    """Change password using current session."""
    payload = {
        "current_password": current_password,
        "new_password": new_password,
        "confirm_password": new_password
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{AUTH_URL}/password/change", json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Password changed successfully")
        print(f"   Message: {data.get('message')}")
        print(f"   Detail: {data.get('detail')}")
        print(f"   Current session active: {data.get('current_session_active')}")
        print(f"   Other sessions invalidated: {data.get('other_sessions_invalidated')}")
        return True, data
    else:
        print(f"❌ Password change failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False, None

def test_protected_endpoint(token, device_name=""):
    """Test accessing a protected endpoint (GET /me)."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{AUTH_URL}/me", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Protected endpoint accessible{' (' + device_name + ')' if device_name else ''}")
        print(f"   User: {data.get('email')}")
        return True, data
    elif response.status_code == 401:
        print(f"✅ Protected endpoint returned 401 Unauthorized{' (' + device_name + ')' if device_name else ''}")
        error_detail = response.json().get('detail', 'No detail provided')
        print(f"   Detail: {error_detail}")
        return False, error_detail
    else:
        print(f"❌ Unexpected response{' (' + device_name + ')' if device_name else ''}: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None

def main():
    """Run Feature #99 validation test."""
    print("="*80)
    print("Feature #99 Validation Test")
    print("Password change invalidates all existing sessions except current")
    print("="*80)

    all_passed = True

    # Step 1: Register a unique user
    print_step(1, "Register a unique test user")
    email, password = register_unique_user()
    if not email:
        print("❌ VALIDATION FAILED: Could not register user")
        return False

    # Step 2: Login from device 1
    print_step(2, "Login from device 1")
    device1_token = login(email, password, "Device 1")
    if not device1_token:
        print("❌ VALIDATION FAILED: Could not login from device 1")
        return False

    # Step 3: Login from device 2
    print_step(3, "Login from device 2")
    device2_token = login(email, password, "Device 2")
    if not device2_token:
        print("❌ VALIDATION FAILED: Could not login from device 2")
        return False

    # Verify both devices can access protected endpoint BEFORE password change
    print_step(4, "Verify both devices can access protected endpoint BEFORE password change")
    success1, _ = test_protected_endpoint(device1_token, "Device 1")
    all_passed = print_result(success1, "Device 1 can access protected endpoint") and all_passed

    success2, _ = test_protected_endpoint(device2_token, "Device 2")
    all_passed = print_result(success2, "Device 2 can access protected endpoint") and all_passed

    # Step 5: From device 1, change password
    print_step(5, "From device 1, change password")
    new_password = "NewTestPassword123!@#"
    success, change_data = change_password(device1_token, password, new_password)
    if not success:
        print("❌ VALIDATION FAILED: Could not change password")
        return False

    # Verify response contains expected fields
    all_passed = print_result(
        change_data.get('current_session_active') == True,
        "Response indicates current session is active"
    ) and all_passed

    all_passed = print_result(
        change_data.get('other_sessions_invalidated', 0) >= 1,
        f"Response indicates {change_data.get('other_sessions_invalidated', 0)} other session(s) invalidated"
    ) and all_passed

    # Step 6: Verify device 1 still logged in (current session)
    print_step(6, "Verify device 1 still logged in (current session should remain active)")
    success1, _ = test_protected_endpoint(device1_token, "Device 1")
    all_passed = print_result(success1, "Device 1 can still access protected endpoint") and all_passed

    if not success1:
        print("❌ CRITICAL: Device 1 (current session) should remain logged in!")
        all_passed = False

    # Step 7: From device 2, attempt to access protected endpoint
    print_step(7, "From device 2, attempt to access protected endpoint (should be logged out)")
    success2, detail = test_protected_endpoint(device2_token, "Device 2")

    # Device 2 should be logged out (401 Unauthorized)
    all_passed = print_result(
        success2 == False,
        "Device 2 received 401 Unauthorized (logged out)"
    ) and all_passed

    if success2:
        print("❌ CRITICAL: Device 2 should be logged out after password change!")
        all_passed = False

    # Step 8: Verify the new password works for login
    print_step(8, "Verify new password works for login")
    new_login_token = login(email, new_password, "New Login")
    all_passed = print_result(new_login_token is not None, "Can login with new password") and all_passed

    # Step 9: Verify old password doesn't work
    print_step(9, "Verify old password no longer works")
    old_password_token = login(email, password, "Old Password")
    all_passed = print_result(old_password_token is None, "Cannot login with old password") and all_passed

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nFeature #99 Implementation:")
        print("- Password change preserves current session ✓")
        print("- Password change invalidates all other sessions ✓")
        print("- Device 1 (current) remains logged in ✓")
        print("- Device 2 (other) gets logged out ✓")
        print("- New password works for login ✓")
        print("- Old password no longer works ✓")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the test output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
