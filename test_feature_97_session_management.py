#!/usr/bin/env python3
"""
Test Feature #97: Session management UI - view and revoke active sessions

Test Steps:
1. Login from multiple devices
2. Navigate to /settings/sessions (GET /sessions)
3. Verify list of active sessions displayed
4. Verify each session shows: device, location, IP, last active time
5. Click 'Revoke' on one session (DELETE /sessions/:id)
6. Verify session removed from list
7. Verify that device logged out
8. Click 'Revoke all other sessions' (DELETE /sessions/all/others)
9. Verify only current session remains
"""

import requests
import json
import time
import subprocess

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"

def test_session_management():
    """Test session management UI."""
    print("=" * 80)
    print("Test Feature #97: Session management UI")
    print("=" * 80)
    
    # Step 1: Register and verify user
    print("\nStep 0: Register a test user...")
    email = f"session_mgmt_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Session Management Test User"
        }
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    user_data = register_response.json()
    user_id = user_data["id"]
    print(f"✅ User registered: {email}")
    
    # Verify user
    verify_cmd = f"""PGPASSWORD=autograph_dev_password psql -h localhost -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE id = '{user_id}';" """
    subprocess.run(verify_cmd, shell=True, capture_output=True)
    print(f"✅ User verified")
    
    # Step 1: Login from multiple devices (3 devices)
    print("\nStep 1: Login from 3 devices...")
    tokens = []
    
    for device_num in range(1, 4):
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": email, "password": password}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login from device {device_num} failed: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        tokens.append(token)
        print(f"✅ Device {device_num} logged in")
        time.sleep(0.2)
    
    # Step 2-4: GET /sessions - list all sessions
    print("\nStep 2-4: List all active sessions...")
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    sessions_response = requests.get(f"{AUTH_SERVICE_URL}/sessions", headers=headers)
    
    if sessions_response.status_code != 200:
        print(f"❌ Failed to list sessions: {sessions_response.text}")
        return False
    
    sessions_data = sessions_response.json()
    sessions = sessions_data["sessions"]
    
    print(f"✅ Retrieved {len(sessions)} sessions")
    print(f"   Total: {sessions_data['total']}")
    
    # Verify session metadata
    for i, session in enumerate(sessions, 1):
        print(f"\n   Session {i}:")
        print(f"     Token ID: {session['token_id']}")
        print(f"     Device: {session['device']}")
        print(f"     Browser: {session['browser']}")
        print(f"     OS: {session['os']}")
        print(f"     IP: {session['ip_address']}")
        print(f"     Created: {session['created_at']}")
        print(f"     Last Activity: {session['last_activity']}")
        print(f"     Is Current: {session['is_current']}")
        
        # Verify required fields exist
        if not all([session.get('device'), session.get('ip_address'), session.get('last_activity')]):
            print(f"❌ Session missing required fields")
            return False
    
    if len(sessions) != 3:
        print(f"❌ Expected 3 sessions, got {len(sessions)}")
        return False
    
    print(f"\n✅ All sessions have required metadata")
    
    # Step 5-7: Revoke device 2's session
    print("\nStep 5-7: Revoke device 2's session...")
    device2_session = next((s for s in sessions if not s['is_current']), None)
    if not device2_session:
        print(f"❌ Could not find a non-current session to revoke")
        return False
    
    # Use the full token for deletion (we stored it in the response)
    token_to_revoke = device2_session['full_token']
    token_id_to_revoke = device2_session['token_id']
    
    # Revoke using device 1's token
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    revoke_response = requests.delete(
        f"{AUTH_SERVICE_URL}/sessions/{token_to_revoke}",
        headers=headers
    )
    
    if revoke_response.status_code != 200:
        print(f"❌ Failed to revoke session: {revoke_response.text}")
        return False
    
    print(f"✅ Session revoked: {token_id_to_revoke}")
    
    # Verify session is gone
    sessions_response = requests.get(f"{AUTH_SERVICE_URL}/sessions", headers=headers)
    sessions_data = sessions_response.json()
    sessions = sessions_data["sessions"]
    
    if len(sessions) != 2:
        print(f"❌ Expected 2 sessions after revocation, got {len(sessions)}")
        return False
    
    print(f"✅ Session removed from list (2 sessions remain)")
    
    # Try to use revoked token
    headers_revoked = {"Authorization": f"Bearer {token_to_revoke}"}
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers_revoked)
    
    if me_response.status_code == 401:
        print(f"✅ Revoked session properly rejected (401)")
    else:
        print(f"❌ Revoked session still works: {me_response.status_code}")
        return False
    
    # Step 8-9: Revoke all other sessions
    print("\nStep 8-9: Revoke all other sessions (keep only current)...")
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    revoke_all_response = requests.delete(
        f"{AUTH_SERVICE_URL}/sessions/all/others",
        headers=headers
    )
    
    if revoke_all_response.status_code != 200:
        print(f"❌ Failed to revoke all other sessions: {revoke_all_response.text}")
        return False
    
    revoke_data = revoke_all_response.json()
    print(f"✅ Revoked {revoke_data['revoked_count']} session(s)")
    
    # Verify only current session remains
    sessions_response = requests.get(f"{AUTH_SERVICE_URL}/sessions", headers=headers)
    sessions_data = sessions_response.json()
    sessions = sessions_data["sessions"]
    
    if len(sessions) != 1:
        print(f"❌ Expected 1 session, got {len(sessions)}")
        return False
    
    if not sessions[0]['is_current']:
        print(f"❌ Remaining session is not marked as current")
        return False
    
    print(f"✅ Only current session remains")
    print(f"   Token ID: {sessions[0]['token_id']}")
    print(f"   Is Current: {sessions[0]['is_current']}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_session_management()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ Feature #97 TEST PASSED: Session management works correctly!")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ Feature #97 TEST FAILED")
            print("=" * 80)
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
