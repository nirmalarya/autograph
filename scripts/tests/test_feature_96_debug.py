#!/usr/bin/env python3
"""
Test Feature #96 with Redis debugging
"""

import requests
import json
import time
import redis

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def check_redis_sessions(user_id):
    """Check sessions in Redis for a user."""
    user_sessions_key = f"user_sessions:{user_id}"
    tokens = redis_client.smembers(user_sessions_key)
    print(f"  Redis: {len(tokens)} tokens in set {user_sessions_key}")
    
    sessions = []
    for token in tokens:
        session_key = f"session:{token}"
        data = redis_client.get(session_key)
        if data:
            session_data = json.loads(data)
            sessions.append({
                'token': token[:30] + '...',
                'created_at': session_data.get('created_at', 'unknown')
            })
        else:
            print(f"  Redis: Token in set but no session data: {token[:30]}...")
    
    sessions.sort(key=lambda x: x['created_at'])
    for i, sess in enumerate(sessions, 1):
        print(f"    {i}. {sess['token']} @ {sess['created_at']}")
    
    return len(sessions)

def test_concurrent_session_limit():
    """Test concurrent session limit (max 5 sessions per user)."""
    print("=" * 80)
    print("Test Feature #96: Concurrent session limit (DEBUG VERSION)")
    print("=" * 80)
    
    # Register a user
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
    print(f"✅ User registered: {email} (ID: {user_id})")
    
    # Verify user
    import subprocess
    verify_cmd = f"""PGPASSWORD=autograph_dev_password psql -h localhost -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE id = '{user_id}';" """
    subprocess.run(verify_cmd, shell=True, capture_output=True)
    print(f"✅ User verified")
    
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
        
        time.sleep(0.15)  # Delay for different timestamps
    
    print(f"\nRedis check after 5 logins:")
    count = check_redis_sessions(user_id)
    if count != 5:
        print(f"❌ Expected 5 sessions, found {count}")
        return False
    
    # Login from device 6 (should evict device 1)
    print("\nStep 6: Login from device 6 (should evict oldest session)...")
    time.sleep(0.2)
    
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login from device 6 failed: {login_response.text}")
        return False
    
    device6_token = login_response.json()["access_token"]
    tokens.append(device6_token)
    print(f"✅ Device 6 logged in")
    
    print(f"\nRedis check after device 6 login (should still be 5 sessions):")
    count = check_redis_sessions(user_id)
    if count != 5:
        print(f"⚠️  Expected 5 sessions, found {count}")
    
    time.sleep(0.5)
    
    # Test device 1 token
    print("\nTesting device 1 token (should be evicted)...")
    device1_token = tokens[0]
    
    # Check if token still in Redis
    session_key = f"session:{device1_token}"
    if redis_client.exists(session_key):
        print(f"❌ BUG: Device 1 session still exists in Redis!")
        data = redis_client.get(session_key)
        print(f"   Session data: {data}")
    else:
        print(f"✅ Device 1 session deleted from Redis")
    
    # Check if still in user_sessions set
    user_sessions_key = f"user_sessions:{user_id}"
    if redis_client.sismember(user_sessions_key, device1_token):
        print(f"❌ BUG: Device 1 token still in user_sessions set!")
    else:
        print(f"✅ Device 1 token removed from user_sessions set")
    
    # Try to use device 1 token
    headers = {"Authorization": f"Bearer {device1_token}"}
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    
    if me_response.status_code == 401:
        print(f"✅ Device 1 session properly rejected (401)")
        return True
    else:
        print(f"❌ Device 1 session still accepted: {me_response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_concurrent_session_limit()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ Feature #96 TEST PASSED")
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
