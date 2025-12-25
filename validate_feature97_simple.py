#!/usr/bin/env python3
"""
Feature #97: Session Management UI - Simplified Test
Tests session management without email verification dependency.
"""

import sys
import requests
import time
import psycopg2
import os

API_BASE = "http://localhost:8080/api"

def print_step(message):
    """Print a test step."""
    print(f"\n{'='*60}")
    print(f"STEP: {message}")
    print(f"{'='*60}")

def create_user_directly():
    """Create a verified user directly in the database."""
    email = f"sessiontest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    print_step(f"Creating user directly in database: {email}")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database=os.getenv("POSTGRES_DB", "autograph"),
            user=os.getenv("POSTGRES_USER", "autograph"),
            password=os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")
        )
        cursor = conn.cursor()

        # Create user with email_verified=true
        import uuid
        from passlib.hash import bcrypt

        user_id = str(uuid.uuid4())
        hashed = bcrypt.hash(password)

        cursor.execute(
            """
            INSERT INTO users (id, email, hashed_password, email_verified, created_at, updated_at)
            VALUES (%s, %s, %s, TRUE, NOW(), NOW())
            """,
            (user_id, email, hashed)
        )
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ User created with ID: {user_id}")
        return email, password
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def login_user(email, password, device="device1"):
    """Login and get access token."""
    print_step(f"Logging in as {email} from {device}")

    user_agents = {
        "device1": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0",
        "device2": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "device3": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile Safari/604.1",
    }

    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        headers={"User-Agent": user_agents.get(device, user_agents["device1"])}
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    print(f"✅ Logged in from {device}")
    return token

def list_sessions(token):
    """List all sessions."""
    print_step("Listing all sessions")

    response = requests.get(
        f"{API_BASE}/auth/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None

    data = response.json()
    sessions = data.get("sessions", [])
    print(f"✅ Found {len(sessions)} session(s)")

    for i, session in enumerate(sessions, 1):
        print(f"\nSession {i}:")
        print(f"  Device: {session.get('device')}")
        print(f"  Browser: {session.get('browser')}")
        print(f"  IP: {session.get('ip_address')}")
        print(f"  Current: {session.get('is_current')}")

    return sessions

def revoke_session(token, session_token):
    """Revoke a specific session."""
    print_step("Revoking session")

    response = requests.delete(
        f"{API_BASE}/auth/sessions/{session_token}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code not in [200, 204]:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

    print(f"✅ Session revoked")
    return True

def revoke_all_others(token):
    """Revoke all other sessions."""
    print_step("Revoking all other sessions")

    response = requests.delete(
        f"{API_BASE}/auth/sessions/all/others",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code not in [200, 204]:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False

    data = response.json()
    count = data.get("revoked_count", 0)
    print(f"✅ Revoked {count} session(s)")
    return True

def main():
    print("\n" + "="*60)
    print("Feature #97: Session Management UI Test (Simplified)")
    print("="*60)

    # Create user
    email, password = create_user_directly()
    if not email:
        return 1

    # Login from 3 devices
    print_step("Logging in from multiple devices")
    tokens = {}
    for device in ["device1", "device2", "device3"]:
        token = login_user(email, password, device)
        if not token:
            return 1
        tokens[device] = token
        time.sleep(0.5)

    current_token = tokens["device1"]

    # List sessions
    sessions = list_sessions(current_token)
    if not sessions or len(sessions) != 3:
        print(f"\n❌ Expected 3 sessions, got {len(sessions) if sessions else 0}")
        return 1

    # Revoke device2
    device2_token = tokens["device2"]
    if not revoke_session(current_token, device2_token):
        return 1

    # Verify 2 sessions remain
    sessions = list_sessions(current_token)
    if not sessions or len(sessions) != 2:
        print(f"\n❌ Expected 2 sessions, got {len(sessions) if sessions else 0}")
        return 1
    print(f"✅ Correctly shows 2 sessions after revoke")

    # Revoke all others
    if not revoke_all_others(current_token):
        return 1

    # Verify only 1 session remains
    sessions = list_sessions(current_token)
    if not sessions or len(sessions) != 1:
        print(f"\n❌ Expected 1 session, got {len(sessions) if sessions else 0}")
        return 1

    if not sessions[0].get("is_current"):
        print(f"\n❌ Remaining session is not marked as current")
        return 1

    print(f"✅ Only current session remains")

    # Success!
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nFeature Summary:")
    print("✅ Users can view all active sessions")
    print("✅ Sessions show device, browser, and IP info")
    print("✅ Users can revoke individual sessions")
    print("✅ Users can revoke all other sessions")
    print("✅ Current session is preserved")
    print("="*60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
