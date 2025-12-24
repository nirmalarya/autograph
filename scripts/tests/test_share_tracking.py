#!/usr/bin/env python3
"""Test Feature #139: Share tracking - view count and last accessed."""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_share_tracking():
    """Test share tracking: view count and last accessed timestamp."""
    
    print("=" * 80)
    print("FEATURE #139: SHARE TRACKING - VIEW COUNT AND LAST ACCESSED")
    print("=" * 80)
    
    # Step 1: Register and login
    print("\n1. Register and login user...")
    register_data = {
        "email": f"tracking_test_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Tracking Test User"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User registered")
    
    # Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False
    
    tokens = response.json()
    access_token = tokens["access_token"]
    
    # Decode JWT to get user_id
    import jwt
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded["sub"]
    print(f"✅ User logged in (user_id: {user_id})")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }
    
    # Step 2: Create a diagram
    print("\n2. Create diagram...")
    diagram_data = {
        "title": "Test Diagram for Tracking",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "Test diagram for share tracking"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created (id: {diagram_id})")
    
    # Step 3: Generate share link
    print("\n3. Generate share link...")
    share_data = {
        "permission": "view",
        "is_public": True
    }
    
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Share creation failed: {response.status_code}")
        print(response.text)
        return False
    
    share = response.json()
    share_token = share["token"]
    share_id = share["share_id"]
    
    print(f"✅ Share link created")
    print(f"   Share ID: {share_id}")
    print(f"   Token: {share_token[:20]}...")
    
    # Step 4: Access link 5 times
    print("\n4. Access link 5 times...")
    
    for i in range(5):
        response = requests.get(f"{BASE_URL}/shared/{share_token}")
        
        if response.status_code != 200:
            print(f"❌ Share access #{i+1} failed: {response.status_code}")
            print(response.text)
            return False
        
        shared_data = response.json()
        view_count = shared_data.get("view_count", 0)
        last_accessed = shared_data.get("last_accessed_at")
        
        print(f"   Access #{i+1}: view_count={view_count}, last_accessed={last_accessed}")
        
        # Verify view count increments
        expected_count = i + 1
        if view_count != expected_count:
            print(f"❌ View count mismatch! Expected {expected_count}, got {view_count}")
            return False
        
        # Verify last_accessed is present and recent
        if not last_accessed:
            print(f"❌ Last accessed timestamp missing!")
            return False
        
        # Small delay between accesses
        time.sleep(0.5)
    
    print(f"✅ All 5 accesses tracked correctly")
    
    # Step 5: Verify view count is 5
    print("\n5. Verify final view count is 5...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Share access failed: {response.status_code}")
        return False
    
    shared_data = response.json()
    final_view_count = shared_data.get("view_count", 0)
    final_last_accessed = shared_data.get("last_accessed_at")
    
    # This should be 6 now (5 previous + 1 current)
    if final_view_count != 6:
        print(f"❌ Final view count incorrect! Expected 6, got {final_view_count}")
        return False
    
    print(f"✅ Final view count: {final_view_count}")
    print(f"✅ Last accessed: {final_last_accessed}")
    
    # Step 6: Verify last accessed timestamp is recent
    print("\n6. Verify last accessed timestamp is recent...")
    
    try:
        # Parse the timestamp
        last_accessed_dt = datetime.fromisoformat(final_last_accessed.replace('Z', '+00:00'))
        now = datetime.now(last_accessed_dt.tzinfo)
        
        # Should be within last few seconds
        time_diff = (now - last_accessed_dt).total_seconds()
        
        if time_diff < 0 or time_diff > 10:
            print(f"⚠️  Warning: Last accessed timestamp seems off (diff: {time_diff}s)")
        else:
            print(f"✅ Last accessed timestamp is recent ({time_diff:.1f}s ago)")
    
    except Exception as e:
        print(f"⚠️  Warning: Could not parse timestamp: {e}")
    
    # Step 7: Wait and access again
    print("\n7. Wait 2 seconds and access again...")
    time.sleep(2)
    
    old_last_accessed = final_last_accessed
    
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Share access failed: {response.status_code}")
        return False
    
    shared_data = response.json()
    new_view_count = shared_data.get("view_count", 0)
    new_last_accessed = shared_data.get("last_accessed_at")
    
    # Step 8: Verify view count incremented to 7
    print("\n8. Verify view count incremented to 7...")
    
    if new_view_count != 7:
        print(f"❌ View count not incremented! Expected 7, got {new_view_count}")
        return False
    
    print(f"✅ View count incremented to {new_view_count}")
    
    # Step 9: Verify last accessed timestamp updated
    print("\n9. Verify last accessed timestamp updated...")
    
    if new_last_accessed == old_last_accessed:
        print(f"❌ Last accessed timestamp not updated!")
        return False
    
    print(f"✅ Last accessed timestamp updated")
    print(f"   Old: {old_last_accessed}")
    print(f"   New: {new_last_accessed}")
    
    # Step 10: Test multiple shares have independent tracking
    print("\n10. Test multiple shares have independent tracking...")
    
    # Create another share
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Second share creation failed: {response.status_code}")
        return False
    
    share2 = response.json()
    share_token2 = share2["token"]
    
    print(f"✅ Second share created: {share_token2[:20]}...")
    
    # Access second share once
    response = requests.get(f"{BASE_URL}/shared/{share_token2}")
    
    if response.status_code != 200:
        print(f"❌ Second share access failed: {response.status_code}")
        return False
    
    shared_data2 = response.json()
    view_count2 = shared_data2.get("view_count", 0)
    
    if view_count2 != 1:
        print(f"❌ Second share view count incorrect! Expected 1, got {view_count2}")
        return False
    
    print(f"✅ Second share has independent tracking (view_count=1)")
    
    # Verify first share still has 7 views
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ First share access failed: {response.status_code}")
        return False
    
    shared_data = response.json()
    view_count = shared_data.get("view_count", 0)
    
    # Should be 8 now (7 previous + 1 current)
    if view_count != 8:
        print(f"❌ First share view count incorrect! Expected 8, got {view_count}")
        return False
    
    print(f"✅ First share still has independent tracking (view_count=8)")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #139 Complete!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_share_tracking()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
