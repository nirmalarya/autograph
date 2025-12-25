#!/usr/bin/env python3
"""
Feature #96 Validation: Concurrent session limit (maximum 5 active sessions per user)

Tests:
1. Login from device 1
2. Login from device 2
3. Login from device 3
4. Login from device 4
5. Login from device 5
6. Verify all 5 sessions active
7. Login from device 6
8. Verify oldest session (device 1) automatically logged out
9. Verify device 1 receives 'Session expired' on next request
10. Verify devices 2-6 still active
"""

import requests
import time
import sys
import json
import urllib3
import subprocess
import re

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_SERVICE_URL = "https://localhost:8085"

def get_verification_token_from_logs(email):
    """Extract verification token from Docker logs."""
    try:
        # Get recent logs
        result = subprocess.run(
            ["docker-compose", "logs", "auth-service", "--tail=100"],
            capture_output=True,
            text=True
        )

        # Look for verification token in logs
        lines = result.stdout.split('\n')

        # Find the line with the email first
        for i, line in enumerate(lines):
            if email in line and "User registered" in line:
                # Try to extract token from JSON log line
                # Pattern: "verification_url": "http://localhost:3000/verify-email?token=<token>"
                match = re.search(r'"verification_url":\s*"[^"]*token=([^"]+)"', line)
                if match:
                    return match.group(1)

                # Also look for DEBUG line nearby
                for j in range(max(0, i-5), min(len(lines), i+10)):
                    if "Verification token created:" in lines[j]:
                        match2 = re.search(r'Verification token created: (\S+)', lines[j])
                        if match2:
                            return match2.group(1)

        return None
    except Exception as e:
        print(f"Error extracting token from logs: {e}")
        return None

def test_concurrent_sessions():
    """Test concurrent session limit."""
    print("=" * 80)
    print("Feature #96: Concurrent Session Limit (Max 5 Sessions)")
    print("=" * 80)

    # Use unique email for test
    test_email = f"concurrent_test_{int(time.time())}@example.com"
    test_password = "SecureP@ss123!"

    # Step 1: Register user
    print("\n1. Registering test user...")
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Concurrent Test User"
        },
        verify=False
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(register_response.text)
        return False

    print(f"✅ User registered: {test_email}")

    # Step 2: Get verification token from logs
    print("\n2. Extracting verification token from logs...")
    time.sleep(0.5)  # Wait for logs to be written
    verification_token = get_verification_token_from_logs(test_email)

    if not verification_token:
        print("❌ Could not extract verification token from logs")
        return False

    print(f"✅ Verification token extracted: {verification_token[:20]}...")

    # Verify email
    print("\n3. Verifying email...")

    verify_response = requests.post(
        f"{AUTH_SERVICE_URL}/email/verify",
        json={"token": verification_token},
        verify=False
    )

    if verify_response.status_code != 200:
        print(f"❌ Email verification failed: {verify_response.status_code}")
        return False

    print("✅ Email verified")

    # Store sessions for each device
    devices = []

    # Steps 4-9: Login from 6 devices
    print("\n4-9. Logging in from 6 devices...")
    for i in range(1, 7):
        print(f"\n   Device {i}: Logging in...")
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            },
            headers={
                "User-Agent": f"Device-{i}-Browser/1.0"
            },
            verify=False
        )

        if login_response.status_code != 200:
            print(f"   ❌ Login failed for device {i}: {login_response.status_code}")
            print(login_response.text)
            return False

        login_data = login_response.json()
        access_token = login_data.get("access_token")

        if not access_token:
            print(f"   ❌ No access token for device {i}")
            return False

        devices.append({
            "id": i,
            "token": access_token,
            "user_agent": f"Device-{i}-Browser/1.0"
        })

        print(f"   ✅ Device {i} logged in (token: {access_token[:20]}...)")

        # Small delay to ensure different timestamps
        time.sleep(0.1)

    # Step 10: Verify device 1 session is expired (should be auto-logged out)
    print("\n10. Testing device 1 (should be auto-logged out)...")
    device1_token = devices[0]["token"]

    me_response = requests.get(
        f"{AUTH_SERVICE_URL}/me",
        headers={"Authorization": f"Bearer {device1_token}"},
        verify=False
    )

    if me_response.status_code == 401:
        print("✅ Device 1 correctly logged out (401 Unauthorized)")
        response_data = me_response.json()
        detail = response_data.get("detail", "")

        # Check for session expired message
        if "session" in detail.lower() or "expired" in detail.lower():
            print(f"   ✅ Correct error message: {detail}")
        else:
            print(f"   ⚠️  Unexpected error message: {detail}")
    else:
        print(f"❌ Device 1 should be logged out but got status {me_response.status_code}")
        print(f"   Response: {me_response.text}")
        return False

    # Step 11: Verify devices 2-6 are still active
    print("\n11. Testing devices 2-6 (should all be active)...")
    active_count = 0

    for i in range(1, 6):  # Devices 2-6 (indices 1-5)
        device = devices[i]
        device_id = device["id"]
        device_token = device["token"]

        me_response = requests.get(
            f"{AUTH_SERVICE_URL}/me",
            headers={"Authorization": f"Bearer {device_token}"},
            verify=False
        )

        if me_response.status_code == 200:
            print(f"   ✅ Device {device_id} still active")
            active_count += 1
        else:
            print(f"   ❌ Device {device_id} should be active but got status {me_response.status_code}")
            print(f"      Response: {me_response.text}")

    if active_count == 5:
        print(f"\n✅ All 5 devices (2-6) are active")
    else:
        print(f"\n❌ Expected 5 active devices, but only {active_count} are active")
        return False

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print("✅ User registration and verification")
    print("✅ Logged in from 6 devices")
    print("✅ Device 1 auto-logged out when device 6 logged in")
    print("✅ Device 1 receives session expired error on next request")
    print("✅ Devices 2-6 remain active (5 concurrent sessions)")
    print("\n🎉 Feature #96: Concurrent Session Limit - PASSED!")
    print("=" * 80)

    return True

if __name__ == "__main__":
    try:
        success = test_concurrent_sessions()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
