#!/usr/bin/env python3
"""
Test Feature #95: Session timeout after 30 minutes of inactivity

Test Steps:
1. Login and access dashboard
2. Wait 29 minutes without activity
3. Perform action
4. Verify session still valid
5. Wait 31 minutes without activity
6. Attempt to perform action
7. Verify 401 Unauthorized response
8. Verify redirect to login with message: 'Session expired due to inactivity'
"""

import requests
import json
import time
from datetime import datetime, timedelta
import redis

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Initialize Redis client to manually manipulate session timestamps
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

def test_session_timeout():
    """Test session timeout after 30 minutes of inactivity."""
    print("=" * 80)
    print("Test Feature #95: Session timeout after 30 minutes of inactivity")
    print("=" * 80)
    
    # Step 1: Register and login
    print("\nStep 1: Register and login...")
    email = f"timeout_test_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Timeout Test User"
        }
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    user_data = register_response.json()
    user_id = user_data["id"]
    print(f"✅ User registered: {email}")
    
    # Get verification token from database/logs and verify email
    # For testing, we'll manually verify the user
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine("postgresql://autograph:autograph_dev_password@localhost:5432/autograph")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Manually verify user
    db.execute(text(f"UPDATE users SET is_verified = true WHERE id = '{user_id}'"))
    db.commit()
    db.close()
    print(f"✅ User verified (manual)")
    
    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    print(f"✅ Login successful, access token: {access_token[:20]}...")
    
    # Step 2: Test that session works immediately
    print("\nStep 2: Test immediate access (session should be valid)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    if me_response.status_code == 200:
        print(f"✅ Session valid: Can access /me endpoint")
    else:
        print(f"❌ Session invalid: {me_response.status_code} - {me_response.text}")
        return False
    
    # Step 3: Manually set last_activity to 29 minutes ago (should still work)
    print("\nStep 3: Simulate 29 minutes of inactivity...")
    session_key = f"session:{access_token}"
    session_data = redis_client.get(session_key)
    
    if not session_data:
        print(f"❌ Session not found in Redis")
        return False
    
    session_dict = json.loads(session_data)
    # Set last_activity to 29 minutes ago
    twenty_nine_min_ago = (datetime.utcnow() - timedelta(minutes=29)).isoformat()
    session_dict["last_activity"] = twenty_nine_min_ago
    
    # Update Redis with modified timestamp, preserving TTL
    ttl = redis_client.ttl(session_key)
    redis_client.setex(session_key, ttl, json.dumps(session_dict))
    print(f"✅ Session last_activity set to 29 minutes ago: {twenty_nine_min_ago}")
    
    # Step 4: Perform action (should still work)
    print("\nStep 4: Perform action after 29 minutes (should still work)...")
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    
    if me_response.status_code == 200:
        print(f"✅ Session still valid after 29 minutes: {me_response.json()['email']}")
        
        # Verify last_activity was updated
        updated_session = json.loads(redis_client.get(session_key))
        updated_time = datetime.fromisoformat(updated_session["last_activity"])
        now = datetime.utcnow()
        seconds_diff = (now - updated_time).total_seconds()
        
        if seconds_diff < 5:  # Should be very recent (within 5 seconds)
            print(f"✅ Last activity timestamp was updated: {updated_session['last_activity']}")
        else:
            print(f"⚠️ Last activity timestamp not updated as expected: {seconds_diff}s ago")
    else:
        print(f"❌ Session expired unexpectedly after 29 minutes: {me_response.status_code}")
        print(f"   Response: {me_response.text}")
        return False
    
    # Step 5: Manually set last_activity to 31 minutes ago (should fail)
    print("\nStep 5: Simulate 31 minutes of inactivity...")
    session_data = redis_client.get(session_key)
    session_dict = json.loads(session_data)
    
    # Set last_activity to 31 minutes ago
    thirty_one_min_ago = (datetime.utcnow() - timedelta(minutes=31)).isoformat()
    session_dict["last_activity"] = thirty_one_min_ago
    
    # Update Redis with modified timestamp
    ttl = redis_client.ttl(session_key)
    redis_client.setex(session_key, ttl, json.dumps(session_dict))
    print(f"✅ Session last_activity set to 31 minutes ago: {thirty_one_min_ago}")
    
    # Step 6: Attempt to perform action (should fail with 401)
    print("\nStep 6: Attempt action after 31 minutes (should fail)...")
    me_response = requests.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
    
    if me_response.status_code == 401:
        response_data = me_response.json()
        error_detail = response_data.get("detail", "")
        
        if "inactivity" in error_detail.lower():
            print(f"✅ Session expired correctly: {error_detail}")
            
            # Step 7: Verify session was deleted from Redis
            session_exists = redis_client.exists(session_key)
            if session_exists == 0:
                print(f"✅ Session was deleted from Redis")
            else:
                print(f"⚠️ Session still exists in Redis (should be deleted)")
            
            return True
        else:
            print(f"⚠️ Got 401 but wrong error message: {error_detail}")
            return False
    else:
        print(f"❌ Session did not expire after 31 minutes: {me_response.status_code}")
        print(f"   Response: {me_response.text}")
        return False

if __name__ == "__main__":
    try:
        success = test_session_timeout()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ Feature #95 TEST PASSED: Session timeout after 30 minutes works correctly!")
            print("=" * 80)
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
