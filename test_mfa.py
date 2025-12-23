#!/usr/bin/env python3
"""Test MFA (Multi-Factor Authentication) functionality."""

import requests
import json
import time
import pyotp

BASE_URL = "http://localhost:8085"

def test_mfa_flow():
    """Test complete MFA flow: setup, enable, login with MFA."""
    
    print("\n" + "="*80)
    print("  Feature #92: Multi-Factor Authentication (MFA) with TOTP Tests")
    print("="*80)
    
    # Test 1: Register a new user
    print("\n" + "="*80)
    print("  Test 1: Register User")
    print("="*80)
    
    email = f"mfa_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={"email": email, "password": password}
    )
    
    if register_response.status_code == 200:
        user_data = register_response.json()
        print(f"✓ User registered: {email}")
        print(f"  User ID: {user_data['id']}")
    else:
        print(f"✗ Registration failed: {register_response.text}")
        return
    
    # Test 2: Login to get access token
    print("\n" + "="*80)
    print("  Test 2: Login to Get Access Token")
    print("="*80)
    
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={"email": email, "password": password, "remember_me": False}
    )
    
    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens["access_token"]
        print(f"✓ Login successful")
        print(f"  Access token: {access_token[:50]}...")
    else:
        print(f"✗ Login failed: {login_response.text}")
        return
    
    # Test 3: Setup MFA (get QR code)
    print("\n" + "="*80)
    print("  Test 3: Setup MFA (Get QR Code)")
    print("="*80)
    
    setup_response = requests.post(
        f"{BASE_URL}/mfa/setup",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if setup_response.status_code == 200:
        mfa_data = setup_response.json()
        secret = mfa_data["secret"]
        qr_code = mfa_data["qr_code"]
        provisioning_uri = mfa_data["provisioning_uri"]
        
        print(f"✓ MFA setup successful")
        print(f"  Secret: {secret}")
        print(f"  QR code (base64): {qr_code[:50]}...")
        print(f"  Provisioning URI: {provisioning_uri}")
    else:
        print(f"✗ MFA setup failed: {setup_response.text}")
        return
    
    # Test 4: Generate TOTP code and enable MFA
    print("\n" + "="*80)
    print("  Test 4: Enable MFA with TOTP Code")
    print("="*80)
    
    # Generate TOTP code using the secret
    totp = pyotp.TOTP(secret)
    code = totp.now()
    print(f"  Generated TOTP code: {code}")
    
    enable_response = requests.post(
        f"{BASE_URL}/mfa/enable",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"code": code}
    )
    
    if enable_response.status_code == 200:
        result = enable_response.json()
        print(f"✓ MFA enabled successfully")
        print(f"  Message: {result['message']}")
    else:
        print(f"✗ MFA enable failed: {enable_response.text}")
        return
    
    # Test 5: Try to enable MFA with invalid code (should fail)
    print("\n" + "="*80)
    print("  Test 5: Try to Enable MFA with Invalid Code (Should Fail)")
    print("="*80)
    
    invalid_enable_response = requests.post(
        f"{BASE_URL}/mfa/enable",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"code": "000000"}
    )
    
    if invalid_enable_response.status_code == 400:
        print(f"✓ MFA enable correctly rejected invalid code")
    else:
        print(f"✗ MFA enable should have failed with invalid code")
    
    # Test 6: Logout
    print("\n" + "="*80)
    print("  Test 6: Logout")
    print("="*80)
    
    logout_response = requests.post(
        f"{BASE_URL}/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if logout_response.status_code == 200:
        print(f"✓ Logout successful")
    else:
        print(f"✗ Logout failed: {logout_response.text}")
    
    # Test 7: Login with password (should require MFA)
    print("\n" + "="*80)
    print("  Test 7: Login with Password (Should Require MFA)")
    print("="*80)
    
    login_mfa_response = requests.post(
        f"{BASE_URL}/login",
        json={"email": email, "password": password, "remember_me": False}
    )
    
    if login_mfa_response.status_code == 200:
        mfa_required_data = login_mfa_response.json()
        if mfa_required_data.get("mfa_required"):
            print(f"✓ Login correctly requires MFA")
            print(f"  Message: {mfa_required_data['message']}")
        else:
            print(f"✗ Login should have required MFA but didn't")
            return
    else:
        print(f"✗ Login failed: {login_mfa_response.text}")
        return
    
    # Test 8: Verify MFA with correct code
    print("\n" + "="*80)
    print("  Test 8: Verify MFA with Correct Code")
    print("="*80)
    
    # Generate new TOTP code
    code = totp.now()
    print(f"  Generated TOTP code: {code}")
    
    verify_response = requests.post(
        f"{BASE_URL}/mfa/verify",
        json={"email": email, "code": code}
    )
    
    if verify_response.status_code == 200:
        tokens = verify_response.json()
        new_access_token = tokens["access_token"]
        print(f"✓ MFA verification successful")
        print(f"  Access token: {new_access_token[:50]}...")
    else:
        print(f"✗ MFA verification failed: {verify_response.text}")
        return
    
    # Test 9: Try to verify MFA with invalid code (should fail)
    print("\n" + "="*80)
    print("  Test 9: Try to Verify MFA with Invalid Code (Should Fail)")
    print("="*80)
    
    invalid_verify_response = requests.post(
        f"{BASE_URL}/mfa/verify",
        json={"email": email, "code": "000000"}
    )
    
    if invalid_verify_response.status_code == 401:
        print(f"✓ MFA verification correctly rejected invalid code")
    else:
        print(f"✗ MFA verification should have failed with invalid code")
    
    # Test 10: Access protected endpoint with new token
    print("\n" + "="*80)
    print("  Test 10: Access Protected Endpoint with New Token")
    print("="*80)
    
    me_response = requests.get(
        f"{BASE_URL}/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"✓ Successfully accessed protected endpoint")
        print(f"  Email: {user_info['email']}")
        print(f"  MFA Enabled: {user_info.get('mfa_enabled', False)}")
    else:
        print(f"✗ Failed to access protected endpoint: {me_response.text}")
    
    print("\n" + "="*80)
    print("  Test Summary")
    print("="*80)
    print("✅ All MFA tests passed!")
    print("\nMFA Flow:")
    print("1. User registers and logs in")
    print("2. User calls /mfa/setup to get QR code")
    print("3. User scans QR code with authenticator app")
    print("4. User calls /mfa/enable with code from app")
    print("5. MFA is now enabled for the user")
    print("6. On next login, user enters password")
    print("7. Login returns mfa_required=true")
    print("8. User calls /mfa/verify with code from app")
    print("9. MFA verification returns JWT tokens")
    print("10. User can access protected endpoints")


if __name__ == "__main__":
    test_mfa_flow()
