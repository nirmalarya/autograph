#!/usr/bin/env python3
"""Test to verify concurrent session limit with detailed debugging."""

import requests
import json
import time
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

def count_user_sessions(user_id: str) -> int:
    """Count sessions for a user directly from Redis."""
    pattern = "session:*"
    count = 0
    
    for key in redis_client.scan_iter(match=pattern):
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        
        session_data_str = redis_client.get(key)
        if session_data_str:
            session_data = json.loads(session_data_str)
            if session_data.get("user_id") == user_id:
                count += 1
    
    return count

def test_concurrent_limit():
    """Test concurrent session limit with detailed debugging."""
    print("=" * 80)
    print("Detailed Concurrent Session Test")
    print("=" * 80)
    
    # Register user
    print("\n1. Registering user...")
    email = f"debug_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Debug Test User"
        }
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    user_data = register_response.json()
    user_id = user_data["id"]
    print(f"✅ User registered: {user_id}")
    
    # Verify user
    engine = create_engine("postgresql://autograph:autograph_dev_password@localhost:5432/autograph")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    db.execute(text(f"UPDATE users SET is_verified = true WHERE id = '{user_id}'"))
    db.commit()
    db.close()
    print(f"✅ User verified")
    
    # Login 6 times and check session count after each
    tokens = []
    
    for i in range(1, 7):
        print(f"\n2.{i}. Login from device {i}...")
        
        # Check session count BEFORE login
        count_before = count_user_sessions(user_id)
        print(f"   Sessions before login: {count_before}")
        
        # Login
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": email, "password": password}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        token = login_response.json()["access_token"]
        tokens.append(token)
        print(f"✅ Device {i} logged in")
        
        # Check session count AFTER login
        time.sleep(0.2)  # Give Redis time to update
        count_after = count_user_sessions(user_id)
        print(f"   Sessions after login: {count_after}")
        
        if i <= 5:
            expected = i
        else:
            expected = 5  # Should stay at 5
        
        if count_after != expected:
            print(f"⚠️  Expected {expected} sessions, got {count_after}")
        
        time.sleep(0.1)
    
    # Final verification
    print("\n3. Final verification...")
    final_count = count_user_sessions(user_id)
    print(f"   Final session count: {final_count}")
    
    # Test each token
    for i, token in enumerate(tokens, 1):
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
        
        if me_response.status_code == 200:
            print(f"   Device {i}: ✅ Active")
        elif me_response.status_code == 401:
            print(f"   Device {i}: ❌ Expired")
        else:
            print(f"   Device {i}: ⚠️  Unexpected status {me_response.status_code}")
    
    # Expected: Device 1 should be expired, devices 2-6 should be active
    device1_headers = {"Authorization": f"Bearer {tokens[0]}"}
    device1_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=device1_headers)
    
    if device1_response.status_code == 401:
        print("\n✅ Device 1 correctly evicted")
        return True
    else:
        print(f"\n❌ Device 1 still active (status {device1_response.status_code})")
        return False

if __name__ == "__main__":
    success = test_concurrent_limit()
    exit(0 if success else 1)
