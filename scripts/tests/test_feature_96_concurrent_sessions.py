#!/usr/bin/env python3
"""
Test Feature #96: Concurrent session limit - maximum 5 active sessions per user

Test Steps:
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
import json
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"

def test_concurrent_session_limit():
    """Test concurrent session limit (max 5 sessions per user)."""
    print("=" * 80)
    print("Test Feature #96: Concurrent session limit (max 5 sessions)")
    print("=" * 80)
    
    # Step 1: Register a user
    print("\nStep 0: Register a test user...")
    email = f"concurrent_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Concurrent Test User"
        }
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    user_data = register_response.json()
    user_id = user_data["id"]
    print(f"✅ User registered: {email}")
    
    # Manually verify user
    engine = create_engine("postgresql://autograph:autograph_dev_password@localhost:5432/autograph")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    db.execute(text(f"UPDATE users SET is_verified = true WHERE id = '{user_id}'"))
    db.commit()
    db.close()
    print(f"✅ User verified")
    
    # Login from 6 devices
    tokens = []
    
    print("\nStep 1-5: Login from 5 devices...")
    for device_num in range(1, 6):
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": email, "password": password}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login from device {device_num} failed: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        tokens.append(token)
        print(f"✅ Device {device_num} logged in: token {token[:20]}...")
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
    
    # Step 6: Verify all 5 sessions are active
    print("\nStep 6: Verify all 5 sessions are active...")
    for i, token in enumerate(tokens, 1):
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
        
        if me_response.status_code == 200:
            print(f"✅ Device {i} session active: {me_response.json()['email']}")
        else:
            print(f"❌ Device {i} session not active: {me_response.status_code}")
            return False
    
    # Step 7: Login from device 6 (should evict device 1)
    print("\nStep 7: Login from device 6 (should evict oldest session - device 1)...")
    time.sleep(0.2)  # Ensure different timestamp
    
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login from device 6 failed: {login_response.text}")
        return False
    
    device6_token = login_response.json()["access_token"]
    print(f"✅ Device 6 logged in: token {device6_token[:20]}...")
    
    # Give Redis time to process the session eviction
    time.sleep(0.5)
    
    # Step 8-9: Verify device 1 session was evicted
    print("\nStep 8-9: Verify device 1 session was evicted...")
    device1_token = tokens[0]
    headers = {"Authorization": f"Bearer {device1_token}"}
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    
    if me_response.status_code == 401:
        error_detail = me_response.json().get("detail", "")
        print(f"✅ Device 1 session expired (evicted): {error_detail}")
    else:
        print(f"❌ Device 1 session still active (should be evicted): {me_response.status_code}")
        return False
    
    # Step 10: Verify devices 2-6 are still active
    print("\nStep 10: Verify devices 2-6 are still active...")
    active_count = 0
    
    # Check devices 2-5 (indices 1-4)
    for i in range(1, 5):
        headers = {"Authorization": f"Bearer {tokens[i]}"}
        me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
        
        if me_response.status_code == 200:
            active_count += 1
            print(f"✅ Device {i+1} session active")
        else:
            print(f"❌ Device {i+1} session not active: {me_response.status_code}")
            return False
    
    # Check device 6
    headers = {"Authorization": f"Bearer {device6_token}"}
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    
    if me_response.status_code == 200:
        active_count += 1
        print(f"✅ Device 6 session active")
    else:
        print(f"❌ Device 6 session not active: {me_response.status_code}")
        return False
    
    if active_count == 5:
        print(f"\n✅ Exactly 5 sessions active (devices 2-6)")
        return True
    else:
        print(f"\n❌ Expected 5 active sessions, got {active_count}")
        return False

if __name__ == "__main__":
    try:
        success = test_concurrent_session_limit()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ Feature #96 TEST PASSED: Concurrent session limit works correctly!")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ Feature #96 TEST FAILED")
            print("=" * 80)
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
