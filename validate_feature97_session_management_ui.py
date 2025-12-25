#!/usr/bin/env python3
"""
Feature #97: Session Management UI - View and Revoke Active Sessions
Tests the session management user interface functionality.
"""

import sys
import requests
import time
import re
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "http://localhost:8080/api"
FRONTEND_BASE = "http://localhost:3000"

def print_step(message):
    """Print a test step."""
    print(f"\n{'='*60}")
    print(f"STEP: {message}")
    print(f"{'='*60}")

def register_and_verify_user(email, password):
    """Register a new user and verify their email."""
    print_step(f"Registering user: {email}")

    # Register
    response = requests.post(
        f"{API_BASE}/auth/register",
        json={"email": email, "password": password},
        verify=False
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    print(f"✅ User registered: {email}")

    # Wait for email verification token in logs
    print("Waiting for email verification token in logs...")
    time.sleep(2)

    # Get verification token from auth service logs
    import subprocess
    result = subprocess.run(
        ["docker-compose", "logs", "--tail=100", "auth-service"],
        capture_output=True,
        text=True
    )

    # Find verification token in logs - matches both formats:
    # "verification_token": "abc-123"
    # token=abc-123
    token_pattern = r'(?:verification_token["\s:]+|token=)([A-Za-z0-9_-]+)'
    matches = re.findall(token_pattern, result.stdout)

    if not matches:
        print(f"❌ Could not find verification token in logs")
        return None

    verification_token = matches[-1]
    print(f"✅ Found verification token: {verification_token[:20]}...")

    # Verify email
    response = requests.post(
        f"{API_BASE}/auth/email/verify",
        json={"token": verification_token},
        verify=False
    )
    if response.status_code not in [200, 302]:
        print(f"❌ Email verification failed: {response.status_code}")
        return None

    print(f"✅ Email verified successfully")
    return email

def login_from_device(email, password, device_name):
    """Login from a simulated device and return the access token."""
    print_step(f"Logging in from {device_name}")

    # Simulate different user agents for different devices
    user_agents = {
        "device1": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "device2": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "device3": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "device4": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "device5": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Firefox/120.0",
    }

    headers = {
        "User-Agent": user_agents.get(device_name, user_agents["device1"])
    }

    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        headers=headers,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Login failed from {device_name}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    access_token = data.get("access_token")

    if not access_token:
        print(f"❌ No access token received from {device_name}")
        return None

    print(f"✅ Logged in from {device_name}")
    return access_token

def list_sessions(access_token):
    """List all active sessions."""
    print_step("Listing all active sessions")

    response = requests.get(
        f"{API_BASE}/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to list sessions: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    sessions = data.get("sessions", [])

    print(f"✅ Retrieved {len(sessions)} session(s)")

    for i, session in enumerate(sessions, 1):
        print(f"\nSession {i}:")
        print(f"  Device: {session.get('device')}")
        print(f"  Browser: {session.get('browser')}")
        print(f"  OS: {session.get('os')}")
        print(f"  IP: {session.get('ip_address')}")
        print(f"  Last Activity: {session.get('last_activity')}")
        print(f"  Is Current: {session.get('is_current')}")

    return sessions

def revoke_session(access_token, token_to_revoke):
    """Revoke a specific session."""
    print_step(f"Revoking session: {token_to_revoke[:20]}...")

    response = requests.delete(
        f"{API_BASE}/auth/sessions/{token_to_revoke}",
        headers={"Authorization": f"Bearer {access_token}"},
        verify=False
    )

    if response.status_code not in [200, 204]:
        print(f"❌ Failed to revoke session: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    print(f"✅ Session revoked successfully")
    return True

def verify_session_revoked(revoked_token):
    """Verify that a revoked session cannot access protected resources."""
    print_step("Verifying revoked session is logged out")

    response = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {revoked_token}"},
        verify=False
    )

    if response.status_code == 401:
        print(f"✅ Revoked session correctly returns 401 Unauthorized")
        return True
    else:
        print(f"❌ Revoked session still active (status: {response.status_code})")
        return False

def revoke_all_other_sessions(access_token):
    """Revoke all sessions except the current one."""
    print_step("Revoking all other sessions")

    response = requests.delete(
        f"{API_BASE}/auth/sessions/all/others",
        headers={"Authorization": f"Bearer {access_token}"},
        verify=False
    )

    if response.status_code not in [200, 204]:
        print(f"❌ Failed to revoke all other sessions: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()
    revoked_count = data.get("revoked_count", 0)
    print(f"✅ Revoked {revoked_count} session(s)")
    return True

def verify_only_current_session_remains(access_token):
    """Verify that only the current session remains after revoking all others."""
    print_step("Verifying only current session remains")

    sessions = list_sessions(access_token)

    if sessions is None:
        return False

    if len(sessions) != 1:
        print(f"❌ Expected 1 session, found {len(sessions)}")
        return False

    if not sessions[0].get("is_current"):
        print(f"❌ The remaining session is not marked as current")
        return False

    print(f"✅ Only current session remains (count: 1)")
    return True

def main():
    """Main test execution."""
    print("\n" + "="*60)
    print("Feature #97: Session Management UI Test")
    print("="*60)

    # Test data
    email = f"sessiontest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    try:
        # Step 1: Register and verify user
        if not register_and_verify_user(email, password):
            print("\n❌ TEST FAILED: User registration/verification failed")
            return 1

        # Step 2: Login from multiple devices
        print_step("Logging in from multiple devices")
        tokens = {}
        for device in ["device1", "device2", "device3", "device4"]:
            token = login_from_device(email, password, device)
            if not token:
                print(f"\n❌ TEST FAILED: Login from {device} failed")
                return 1
            tokens[device] = token
            time.sleep(0.5)  # Brief pause between logins

        # Use device1 as the current session for testing
        current_token = tokens["device1"]

        # Step 3: List all sessions
        sessions = list_sessions(current_token)
        if sessions is None:
            print("\n❌ TEST FAILED: Could not list sessions")
            return 1

        if len(sessions) != 4:
            print(f"\n❌ TEST FAILED: Expected 4 sessions, found {len(sessions)}")
            return 1

        print(f"✅ All 4 sessions are active")

        # Step 4: Verify session metadata
        print_step("Verifying session metadata")
        required_fields = ["device", "browser", "os", "ip_address", "created_at", "last_activity"]

        for session in sessions:
            for field in required_fields:
                if field not in session:
                    print(f"❌ TEST FAILED: Session missing field: {field}")
                    return 1

        print(f"✅ All sessions have required metadata")

        # Step 5: Revoke one specific session (device2)
        device2_token = tokens["device2"]

        # Find device2's full token from sessions list
        device2_full_token = None
        for session in sessions:
            # Try to match by checking if this token works (we'll use device2_token)
            # Actually, we need to use the full_token from the session
            # Let's just use the device2_token directly
            pass

        if not revoke_session(current_token, device2_token):
            print("\n❌ TEST FAILED: Could not revoke device2 session")
            return 1

        # Step 6: Verify device2 is logged out
        if not verify_session_revoked(device2_token):
            print("\n❌ TEST FAILED: Device2 session not properly revoked")
            return 1

        # Step 7: Verify 3 sessions remain
        sessions = list_sessions(current_token)
        if len(sessions) != 3:
            print(f"\n❌ TEST FAILED: Expected 3 sessions after revoke, found {len(sessions)}")
            return 1

        print(f"✅ 3 sessions remain after revoking device2")

        # Step 8: Revoke all other sessions
        if not revoke_all_other_sessions(current_token):
            print("\n❌ TEST FAILED: Could not revoke all other sessions")
            return 1

        # Step 9: Verify only current session remains
        if not verify_only_current_session_remains(current_token):
            print("\n❌ TEST FAILED: Multiple sessions remain after revoke all")
            return 1

        # Step 10: Verify other devices are logged out
        print_step("Verifying other devices are logged out")
        for device, token in tokens.items():
            if device == "device1":
                continue  # Skip current session

            response = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                verify=False
            )

            if response.status_code != 401:
                print(f"❌ TEST FAILED: {device} is still active (status: {response.status_code})")
                return 1

        print(f"✅ All other devices are logged out")

        # All tests passed!
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - Feature #97 Working Correctly!")
        print("="*60)
        print("\nFeature Summary:")
        print("✅ Users can view all active sessions")
        print("✅ Sessions display device, browser, OS, IP, and timestamps")
        print("✅ Users can revoke individual sessions")
        print("✅ Revoked sessions are immediately logged out")
        print("✅ Users can revoke all other sessions")
        print("✅ Only current session remains after 'revoke all others'")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
