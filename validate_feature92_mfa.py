#!/usr/bin/env python3
"""
Validation script for Feature #92: Multi-factor authentication (MFA) with TOTP
Tests the complete MFA setup and login flow.
"""

import requests
import time
import pyotp
from urllib.parse import parse_qs, urlparse
import re

# Configuration
AUTH_SERVICE = "https://localhost:8085"
API_GATEWAY = "http://localhost:8080"
TEST_EMAIL = f"mfa_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecureP@ss123!"

def test_mfa_flow():
    """Test complete MFA setup and verification flow."""
    print("=" * 60)
    print("FEATURE #92: Multi-factor authentication (MFA) with TOTP")
    print("=" * 60)
    print()

    session = requests.Session()
    session.verify = False  # For self-signed certs

    try:
        # Step 1: Register a new user
        print("Step 1: Registering new user...")
        register_response = session.post(
            f"{AUTH_SERVICE}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "MFA Test User"
            }
        )

        if register_response.status_code != 201:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(f"Response: {register_response.text}")
            return False

        print(f"✅ User registered: {TEST_EMAIL}")

        # Extract verification token from response
        reg_data = register_response.json()
        user_id = reg_data.get("id")

        if not user_id:
            print("❌ No user ID in registration response")
            return False

        # Get verification token from database (for testing purposes)
        import psycopg2
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
            print("❌ Could not find verification token in database")
            return False

        verification_token = result[0]
        print(f"   Retrieved verification token from database")

        # Step 2: Verify email
        print("\nStep 2: Verifying email...")
        verify_response = session.post(
            f"{AUTH_SERVICE}/email/verify",
            json={"token": verification_token}
        )

        if verify_response.status_code != 200:
            print(f"❌ Email verification failed: {verify_response.status_code}")
            print(f"Response: {verify_response.text}")
            return False

        print("✅ Email verified successfully")

        # Step 3: Login to get access token
        print("\nStep 3: Logging in...")
        login_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False

        login_data = login_response.json()
        access_token = login_data.get("access_token")

        if not access_token:
            print("❌ No access token received")
            return False

        print("✅ Login successful")

        # Set authorization header for subsequent requests
        session.headers.update({"Authorization": f"Bearer {access_token}"})

        # Step 4: Setup MFA (navigate to /settings/security equivalent)
        print("\nStep 4: Setting up MFA (GET /mfa/setup)...")
        mfa_setup_response = session.post(
            f"{AUTH_SERVICE}/mfa/setup",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if mfa_setup_response.status_code != 200:
            print(f"❌ MFA setup failed: {mfa_setup_response.status_code}")
            print(f"Response: {mfa_setup_response.text}")
            return False

        setup_data = mfa_setup_response.json()
        secret = setup_data.get("secret")
        qr_code = setup_data.get("qr_code")

        if not secret or not qr_code:
            print("❌ MFA setup response missing secret or QR code")
            return False

        print(f"✅ MFA setup initiated")
        print(f"   Secret: {secret}")
        print(f"   QR Code (base64): {qr_code[:50]}...")

        # Step 5: Generate TOTP code from secret (simulating authenticator app scan)
        print("\nStep 5: Generating TOTP code (simulating authenticator app)...")
        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        print(f"✅ Generated 6-digit code: {current_code}")

        # Step 6: Enable MFA by submitting the code
        print("\nStep 6: Enabling MFA with TOTP code...")
        enable_response = session.post(
            f"{AUTH_SERVICE}/mfa/enable",
            json={"code": current_code},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if enable_response.status_code != 200:
            print(f"❌ MFA enable failed: {enable_response.status_code}")
            print(f"Response: {enable_response.text}")
            return False

        enable_data = enable_response.json()
        print(f"✅ MFA enabled successfully")

        # Check if backup codes were provided
        if "backup_codes" in enable_data:
            print(f"   Backup codes provided: {len(enable_data['backup_codes'])} codes")

        # Step 7: Logout
        print("\nStep 7: Logging out...")
        logout_response = session.post(
            f"{AUTH_SERVICE}/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if logout_response.status_code != 200:
            print(f"⚠️  Logout warning: {logout_response.status_code}")
        else:
            print("✅ Logged out successfully")

        # Clear the session headers
        session.headers.pop("Authorization", None)

        # Step 8: Login again (should now require MFA)
        print("\nStep 8: Logging in again (should prompt for MFA)...")
        login2_response = session.post(
            f"{AUTH_SERVICE}/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )

        # Login should succeed but indicate MFA is required
        if login2_response.status_code != 200:
            print(f"❌ Second login failed: {login2_response.status_code}")
            print(f"Response: {login2_response.text}")
            return False

        login2_data = login2_response.json()

        # Check if MFA is required
        if not login2_data.get("mfa_required"):
            print("❌ Login did not indicate MFA is required")
            print(f"Response: {login2_data}")
            return False

        print("✅ Login prompted for MFA code (mfa_required: true)")

        # Step 9: Generate new TOTP code
        print("\nStep 9: Generating new TOTP code for MFA verification...")
        time.sleep(1)  # Wait to ensure we get a fresh code
        new_code = totp.now()
        print(f"✅ Generated code: {new_code}")

        # Step 10: Verify MFA code
        print("\nStep 10: Verifying MFA code...")
        mfa_verify_response = session.post(
            f"{AUTH_SERVICE}/mfa/verify",
            json={
                "email": TEST_EMAIL,
                "code": new_code
            }
        )

        if mfa_verify_response.status_code != 200:
            print(f"❌ MFA verification failed: {mfa_verify_response.status_code}")
            print(f"Response: {mfa_verify_response.text}")
            return False

        verify_data = mfa_verify_response.json()
        final_access_token = verify_data.get("access_token")

        if not final_access_token:
            print("❌ No access token after MFA verification")
            return False

        print("✅ MFA verification succeeded!")
        print(f"   Received access token: {final_access_token[:20]}...")

        # Step 11: Verify we can access protected endpoints
        print("\nStep 11: Testing access to protected endpoint...")
        me_response = session.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {final_access_token}"}
        )

        if me_response.status_code != 200:
            print(f"❌ Protected endpoint access failed: {me_response.status_code}")
            return False

        user_data = me_response.json()
        print(f"✅ Protected endpoint accessible")
        print(f"   User: {user_data.get('email')}")

        # Verify it's the correct user
        if user_data.get("email") != TEST_EMAIL:
            print("❌ Protected endpoint returned wrong user")
            return False

        print("\n" + "=" * 60)
        print("✅ ALL MFA TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✅ User registration and email verification")
        print("  ✅ MFA setup with QR code and secret")
        print("  ✅ TOTP code generation (simulated authenticator app)")
        print("  ✅ MFA enablement with code verification")
        print("  ✅ Login prompts for MFA when enabled")
        print("  ✅ MFA verification completes login flow")
        print("  ✅ Access granted after successful MFA verification")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_mfa_flow()
    exit(0 if success else 1)
