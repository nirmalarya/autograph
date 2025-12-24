#!/usr/bin/env python3
"""
Test Feature #95: Concurrent session limit - maximum 5 active sessions per user

Test Steps:
1. Register user and verify email
2. Login from 5 devices (should all succeed)
3. Verify all 5 sessions are active
4. Login from 6th device (should evict oldest)
5. Verify oldest session (device 1) is expired
6. Verify devices 2-6 are still active
"""

import requests
import time
import psycopg2

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def test_concurrent_session_limit():
    """Test concurrent session limit (max 5 sessions per user)."""
    print("=" * 80)
    print("Test Feature #95: Concurrent session limit (max 5 sessions)")
    print("=" * 80)
    
    # Step 0: Register a user
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
    
    # Manually verify user via database
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ User verified via database")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Login from 5 devices
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
        print(f"✅ Device {device_num} logged in")
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
    
    # Step 6: Verify all 5 sessions are active
    print("\nStep 6: Verify all 5 sessions are active...")
    for i, token in enumerate(tokens, 1):
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
        
        if me_response.status_code == 200:
            print(f"✅ Device {i} session active")
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
    print(f"✅ Device 6 logged in")
    
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
            print("✅ Feature #95 TEST PASSED: Concurrent session limit works correctly!")
            print("=" * 80)
            print("\nTest Summary:")
            print("  • User can login from 5 devices simultaneously")
            print("  • All 5 sessions remain active")
            print("  • 6th login automatically evicts oldest session")
            print("  • Evicted session returns 401 Unauthorized")
            print("  • Remaining 5 sessions stay active")
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ Feature #95 TEST FAILED")
            print("=" * 80)
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
