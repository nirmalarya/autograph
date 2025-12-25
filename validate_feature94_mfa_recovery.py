#!/usr/bin/env python3
"""
Validation script for Feature #94: MFA recovery - disable MFA if lost device
Tests the ability to disable MFA using backup codes when device is lost.
"""

import requests
import time
import pyotp
import psycopg2

# Configuration
AUTH_SERVICE = "https://localhost:8085"
TEST_EMAIL = f"mfa_recovery_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecureP@ss123!"

def test_mfa_recovery():
    """Test MFA recovery flow when device is lost."""
    print("=" * 70)
    print("FEATURE #94: MFA recovery - disable MFA if lost device")
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
                "name": "MFA Recovery Test User"
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

        # Step 3: Enable MFA
        print("\nStep 3: Enabling MFA for user...")
        mfa_setup_response = session.post(f"{AUTH_SERVICE}/mfa/setup")

        if mfa_setup_response.status_code != 200:
            print(f"❌ MFA setup failed: {mfa_setup_response.status_code}")
            return False

        setup_data = mfa_setup_response.json()
        secret = setup_data.get("secret")

        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        enable_response = session.post(
            f"{AUTH_SERVICE}/mfa/enable",
            json={"code": current_code}
        )

        if enable_response.status_code != 200:
            print(f"❌ MFA enable failed: {enable_response.status_code}")
            return False

        enable_data = enable_response.json()
        backup_codes = enable_data.get("backup_codes", [])

        if not backup_codes or len(backup_codes) != 10:
            print(f"❌ Expected 10 backup codes, got {len(backup_codes)}")
            return False

        print(f"✅ MFA enabled successfully")
        print(f"   Generated {len(backup_codes)} backup codes")

        # Save backup codes for recovery scenario
        saved_backup_code = backup_codes[0]
        print(f"   Saved backup code for recovery: {saved_backup_code}")

        # Step 4: Simulate lost device scenario
        print("\nStep 4: Simulating lost device scenario...")
        print("   📱 Device with authenticator app is lost!")
        print("   ⚠️  Cannot generate TOTP codes anymore")
        print("   ✅ User has saved backup codes")

        # Step 5: Use backup code to disable MFA
        print("\nStep 5: Disabling MFA using backup code (recovery)...")
        print(f"   Using saved backup code: {saved_backup_code}")

        disable_response = session.post(
            f"{AUTH_SERVICE}/mfa/disable",
            json={"code": saved_backup_code}
        )

        if disable_response.status_code != 200:
            print(f"❌ MFA disable failed: {disable_response.status_code}")
            print(f"Response: {disable_response.text}")
            return False

        disable_data = disable_response.json()
        print(f"✅ MFA disabled successfully")
        print(f"   Message: {disable_data.get('message')}")

        # Step 6: Logout
        print("\nStep 6: Logging out...")
        session.post(f"{AUTH_SERVICE}/logout")
        session.headers.pop("Authorization", None)
        print("✅ Logged out")

        # Step 7: Login with just password (no MFA required)
        print("\nStep 7: Logging in with password only (no MFA)...")
        login2_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login2_response.status_code != 200:
            print(f"❌ Login failed: {login2_response.status_code}")
            return False

        login2_data = login2_response.json()

        # Should NOT require MFA anymore
        if login2_data.get("mfa_required"):
            print("❌ Login still requires MFA (should not after disable)")
            return False

        new_access_token = login2_data.get("access_token")
        if not new_access_token:
            print("❌ No access token received")
            return False

        print("✅ Login successful with password only (no MFA required)")

        # Step 8: Verify access to protected endpoint
        print("\nStep 8: Verifying access to protected endpoint...")
        me_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        if me_response.status_code != 200:
            print(f"❌ Protected endpoint access failed: {me_response.status_code}")
            return False

        print("✅ Access granted without MFA")

        # Step 9: Re-enable MFA with new device
        print("\nStep 9: Re-enabling MFA with new device...")
        session.headers.update({"Authorization": f"Bearer {new_access_token}"})

        # Setup MFA again (simulating new device)
        new_setup_response = session.post(f"{AUTH_SERVICE}/mfa/setup")

        if new_setup_response.status_code != 200:
            print(f"❌ New MFA setup failed: {new_setup_response.status_code}")
            return False

        new_setup_data = new_setup_response.json()
        new_secret = new_setup_data.get("secret")

        if new_secret == secret:
            print("⚠️  Warning: New secret is same as old secret (should be different)")

        print(f"✅ New MFA setup initiated")
        print(f"   New secret: {new_secret}")

        # Enable MFA with new device
        new_totp = pyotp.TOTP(new_secret)
        new_code = new_totp.now()

        new_enable_response = session.post(
            f"{AUTH_SERVICE}/mfa/enable",
            json={"code": new_code}
        )

        if new_enable_response.status_code != 200:
            print(f"❌ New MFA enable failed: {new_enable_response.status_code}")
            print(f"Response: {new_enable_response.text}")
            return False

        new_enable_data = new_enable_response.json()
        new_backup_codes = new_enable_data.get("backup_codes", [])

        print(f"✅ MFA re-enabled with new device")
        print(f"   New backup codes generated: {len(new_backup_codes)}")

        # Step 10: Verify MFA is working with new device
        print("\nStep 10: Verifying MFA works with new device...")

        # Logout
        session.post(f"{AUTH_SERVICE}/logout")
        session.headers.pop("Authorization", None)

        # Login (should require MFA)
        login3_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )

        if login3_response.status_code != 200:
            print(f"❌ Login failed: {login3_response.status_code}")
            return False

        login3_data = login3_response.json()

        if not login3_data.get("mfa_required"):
            print("❌ MFA not required (should be required after re-enable)")
            return False

        print("✅ Login requires MFA (as expected)")

        # Verify with new device TOTP
        time.sleep(1)  # Ensure fresh code
        new_verify_code = new_totp.now()

        verify_response = session.post(
            f"{AUTH_SERVICE}/mfa/verify",
            json={"email": TEST_EMAIL, "code": new_verify_code}
        )

        if verify_response.status_code != 200:
            print(f"❌ MFA verification with new device failed: {verify_response.status_code}")
            print(f"Response: {verify_response.text}")
            return False

        print("✅ MFA verification successful with new device")

        print("\n" + "=" * 70)
        print("✅ ALL MFA RECOVERY TESTS PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ MFA enabled for user")
        print("  ✅ Backup codes saved")
        print("  ✅ Lost device scenario simulated")
        print("  ✅ MFA disabled using backup code (recovery)")
        print("  ✅ Login works with password only (no MFA)")
        print("  ✅ MFA re-enabled with new device")
        print("  ✅ New backup codes generated")
        print("  ✅ MFA verification works with new device")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_mfa_recovery()
    exit(0 if success else 1)
