#!/usr/bin/env python3
"""
Validation script for Feature #93: MFA backup codes for account recovery
Tests backup code generation, usage, and one-time-use enforcement.
"""

import requests
import time
import pyotp
import psycopg2

# Configuration
AUTH_SERVICE = "https://localhost:8085"
TEST_EMAIL = f"backup_codes_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecureP@ss123!"

def test_backup_codes():
    """Test MFA backup codes for account recovery."""
    print("=" * 70)
    print("FEATURE #93: MFA backup codes for account recovery")
    print("=" * 70)
    print()

    session = requests.Session()
    session.verify = False  # For self-signed certs

    try:
        # Step 1: Register and verify user
        print("Step 1: Registering and verifying user...")
        register_response = session.post(
            f"{AUTH_SERVICE}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Backup Codes Test User"
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

        # Step 2: Login
        print("\nStep 2: Logging in...")
        login_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False

        access_token = login_response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {access_token}"})
        print("✅ Login successful")

        # Step 3: Setup MFA
        print("\nStep 3: Setting up MFA...")
        mfa_setup_response = session.post(f"{AUTH_SERVICE}/mfa/setup")

        if mfa_setup_response.status_code != 200:
            print(f"❌ MFA setup failed: {mfa_setup_response.status_code}")
            return False

        setup_data = mfa_setup_response.json()
        secret = setup_data.get("secret")
        print("✅ MFA setup initiated")

        # Step 4: Enable MFA and generate backup codes
        print("\nStep 4: Enabling MFA (generates backup codes)...")
        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        enable_response = session.post(
            f"{AUTH_SERVICE}/mfa/enable",
            json={"code": current_code}
        )

        if enable_response.status_code != 200:
            print(f"❌ MFA enable failed: {enable_response.status_code}")
            print(f"Response: {enable_response.text}")
            return False

        enable_data = enable_response.json()
        backup_codes = enable_data.get("backup_codes", [])

        if not backup_codes:
            print("❌ No backup codes in response")
            return False

        print(f"✅ MFA enabled successfully")

        # Step 5: Verify 10 backup codes displayed
        print("\nStep 5: Verifying backup codes...")
        if len(backup_codes) != 10:
            print(f"❌ Expected 10 backup codes, got {len(backup_codes)}")
            return False

        print(f"✅ 10 backup codes generated:")
        for i, code in enumerate(backup_codes, 1):
            print(f"   {i}. {code}")

        # Save first backup code for testing
        test_backup_code = backup_codes[0]
        print(f"\n✅ Saved backup code for testing: {test_backup_code}")

        # Step 6: Logout
        print("\nStep 6: Logging out...")
        session.post(f"{AUTH_SERVICE}/logout")
        session.headers.pop("Authorization", None)
        print("✅ Logged out")

        # Step 7: Login again (will require MFA)
        print("\nStep 7: Logging in again...")
        login2_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login2_response.status_code != 200:
            print(f"❌ Login failed: {login2_response.status_code}")
            return False

        login2_data = login2_response.json()
        if not login2_data.get("mfa_required"):
            print("❌ MFA not required on login")
            return False

        print("✅ Login requires MFA verification")

        # Step 8: Use backup code instead of TOTP
        print("\nStep 8: Verifying with backup code instead of TOTP...")
        print(f"   Using backup code: {test_backup_code}")

        backup_verify_response = session.post(
            f"{AUTH_SERVICE}/mfa/verify",
            json={
                "email": TEST_EMAIL,
                "code": test_backup_code
            }
        )

        if backup_verify_response.status_code != 200:
            print(f"❌ Backup code verification failed: {backup_verify_response.status_code}")
            print(f"Response: {backup_verify_response.text}")
            return False

        verify_data = backup_verify_response.json()
        new_access_token = verify_data.get("access_token")

        if not new_access_token:
            print("❌ No access token after backup code verification")
            return False

        print("✅ Backup code verification succeeded!")
        print(f"   Received access token")

        # Step 9: Verify we can access protected endpoints
        print("\nStep 9: Testing access to protected endpoint...")
        me_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        if me_response.status_code != 200:
            print(f"❌ Protected endpoint access failed: {me_response.status_code}")
            return False

        print("✅ Protected endpoint accessible with backup code login")

        # Step 10: Logout and try to reuse the same backup code
        print("\nStep 10: Logging out to test backup code reuse...")
        session.post(
            f"{AUTH_SERVICE}/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        print("✅ Logged out")

        # Step 11: Login again
        print("\nStep 11: Logging in again to test backup code reuse...")
        login3_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login3_response.status_code != 200:
            print(f"❌ Login failed: {login3_response.status_code}")
            return False

        print("✅ Login successful (MFA required)")

        # Step 12: Attempt to reuse same backup code
        print("\nStep 12: Attempting to reuse same backup code...")
        print(f"   Trying to reuse: {test_backup_code}")

        reuse_response = session.post(
            f"{AUTH_SERVICE}/mfa/verify",
            json={
                "email": TEST_EMAIL,
                "code": test_backup_code
            }
        )

        # Should fail (401 Unauthorized)
        if reuse_response.status_code == 200:
            print("❌ Backup code reuse succeeded (should have failed!)")
            return False

        if reuse_response.status_code != 401:
            print(f"⚠️  Expected 401, got {reuse_response.status_code}")

        error_detail = reuse_response.json().get("detail", "")
        print(f"✅ Backup code reuse blocked: {error_detail}")

        # Verify error message mentions backup code or invalid code
        if "backup code" not in error_detail.lower() and "invalid" not in error_detail.lower():
            print(f"⚠️  Error message doesn't mention backup code or invalid: {error_detail}")
        else:
            print("✅ Error message indicates invalid/used backup code")

        # Step 13: Verify we can still use a different backup code
        print("\nStep 13: Testing with a different (unused) backup code...")
        second_backup_code = backup_codes[1]  # Use second backup code
        print(f"   Using backup code: {second_backup_code}")

        second_verify_response = session.post(
            f"{AUTH_SERVICE}/mfa/verify",
            json={
                "email": TEST_EMAIL,
                "code": second_backup_code
            }
        )

        if second_verify_response.status_code != 200:
            print(f"❌ Second backup code verification failed: {second_verify_response.status_code}")
            print(f"Response: {second_verify_response.text}")
            return False

        print("✅ Different backup code works correctly")

        print("\n" + "=" * 70)
        print("✅ ALL BACKUP CODE TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ MFA enablement generates 10 backup codes")
        print("  ✅ Backup codes displayed to user")
        print("  ✅ Backup code works for MFA verification (instead of TOTP)")
        print("  ✅ Login succeeds with backup code")
        print("  ✅ Backup code is one-time-use (reuse blocked)")
        print("  ✅ Different backup codes work independently")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_backup_codes()
    exit(0 if success else 1)
