#!/usr/bin/env python3
"""Test Feature #153: Recent diagrams view."""
import requests
import time
import sys
import base64
import json

BASE_URL_AUTH = "http://localhost:8085"
BASE_URL_DIAGRAM = "http://localhost:8082"

def test_recent_diagrams():
    """Test recent diagrams endpoint."""
    print("=" * 80)
    print("TEST: Feature #153 - Recent Diagrams View")
    print("=" * 80)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    timestamp = int(time.time())
    email = f"test_recent_{timestamp}@example.com"
    password = "TestPassword123!"
    
    register_resp = requests.post(
        f"{BASE_URL_AUTH}/register",
        json={"email": email, "password": password}
    )
    
    if register_resp.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_resp.status_code}")
        print(f"Response: {register_resp.text}")
        return False
    
    print(f"✓ User registered: {email}")
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_resp = requests.post(
        f"{BASE_URL_AUTH}/login",
        json={"email": email, "password": password}
    )
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        print(f"Response: {login_resp.text}")
        return False
    
    login_data = login_resp.json()
    token = login_data["access_token"]
    
    # Decode JWT to get user ID
    # JWT format: header.payload.signature
    payload = token.split('.')[1]
    # Add padding if needed
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    decoded = base64.b64decode(payload)
    token_data = json.loads(decoded)
    user_id = token_data["sub"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    print(f"✓ Login successful")
    print(f"  User ID: {user_id}")
    
    # Step 3: Create 15 diagrams
    print("\n3. Creating 15 test diagrams...")
    diagram_ids = []
    for i in range(15):
        resp = requests.post(
            f"{BASE_URL_DIAGRAM}/",
            json={
                "title": f"Test Diagram {i+1}",
                "file_type": "canvas",
                "canvas_data": {"shapes": []}
            },
            headers=headers
        )
        
        if resp.status_code not in [200, 201]:
            print(f"❌ Failed to create diagram {i+1}: {resp.status_code}")
            return False
        
        diagram_ids.append(resp.json()["id"])
    
    print(f"✓ Created 15 diagrams")
    
    # Step 4: Access diagrams 1-10 (to set last_accessed_at)
    print("\n4. Accessing diagrams 1-10...")
    for i in range(10):
        diagram_id = diagram_ids[i]
        resp = requests.get(
            f"{BASE_URL_DIAGRAM}/{diagram_id}",
            headers=headers
        )
        
        if resp.status_code != 200:
            print(f"❌ Failed to access diagram {i+1}: {resp.status_code}")
            return False
        
        # Small delay to ensure different timestamps
        time.sleep(0.1)
    
    print(f"✓ Accessed diagrams 1-10")
    
    # Step 5: Check recent endpoint
    print("\n5. Checking /recent endpoint...")
    recent_resp = requests.get(
        f"{BASE_URL_DIAGRAM}/recent",
        headers=headers
    )
    
    if recent_resp.status_code != 200:
        print(f"❌ Recent endpoint failed: {recent_resp.status_code}")
        print(f"Response: {recent_resp.text}")
        return False
    
    recent_data = recent_resp.json()
    recent_diagrams = recent_data["diagrams"]
    
    print(f"✓ Recent endpoint returned {len(recent_diagrams)} diagrams")
    
    # Step 6: Verify only 10 diagrams returned
    print("\n6. Verifying only 10 most recent diagrams shown...")
    if len(recent_diagrams) != 10:
        print(f"❌ Expected 10 diagrams, got {len(recent_diagrams)}")
        return False
    
    print(f"✓ Exactly 10 diagrams returned")
    
    # Step 7: Verify sorted by last accessed time
    print("\n7. Verifying sorted by last accessed time...")
    last_accessed_times = [d.get("last_accessed_at") for d in recent_diagrams]
    
    # Check all have last_accessed_at
    if None in last_accessed_times:
        print(f"❌ Some diagrams missing last_accessed_at")
        return False
    
    # Check sorted descending (most recent first)
    is_sorted = all(
        last_accessed_times[i] >= last_accessed_times[i+1]
        for i in range(len(last_accessed_times)-1)
    )
    
    if not is_sorted:
        print(f"❌ Diagrams not sorted by last_accessed_at")
        print(f"Timestamps: {last_accessed_times}")
        return False
    
    print(f"✓ Diagrams sorted by last accessed time (most recent first)")
    print(f"  First accessed: {last_accessed_times[0]}")
    print(f"  Last accessed: {last_accessed_times[-1]}")
    
    # Step 8: Access diagram 11
    print("\n8. Accessing diagram 11...")
    diagram_11_id = diagram_ids[10]  # 0-indexed
    resp = requests.get(
        f"{BASE_URL_DIAGRAM}/{diagram_11_id}",
        headers=headers
    )
    
    if resp.status_code != 200:
        print(f"❌ Failed to access diagram 11: {resp.status_code}")
        return False
    
    print(f"✓ Accessed diagram 11")
    time.sleep(0.2)  # Ensure timestamp is newer
    
    # Step 9: Verify diagram 11 now in recent list
    print("\n9. Verifying diagram 11 now in recent list...")
    recent_resp = requests.get(
        f"{BASE_URL_DIAGRAM}/recent",
        headers=headers
    )
    
    if recent_resp.status_code != 200:
        print(f"❌ Recent endpoint failed: {recent_resp.status_code}")
        return False
    
    recent_data = recent_resp.json()
    recent_diagrams = recent_data["diagrams"]
    recent_ids = [d["id"] for d in recent_diagrams]
    
    if diagram_11_id not in recent_ids:
        print(f"❌ Diagram 11 not in recent list")
        print(f"Recent IDs: {recent_ids}")
        return False
    
    print(f"✓ Diagram 11 is in recent list")
    
    # Verify it's at the top (most recent)
    if recent_ids[0] != diagram_11_id:
        print(f"⚠ Warning: Diagram 11 not at top of list (expected most recent)")
    else:
        print(f"✓ Diagram 11 is at top of list (most recent)")
    
    # Step 10: Verify oldest diagram removed
    print("\n10. Verifying oldest diagram removed from list...")
    # The oldest accessed diagram was diagram 1 (diagram_ids[0])
    oldest_id = diagram_ids[0]
    
    if oldest_id in recent_ids:
        print(f"❌ Oldest diagram still in recent list")
        return False
    
    print(f"✓ Oldest diagram removed from list")
    
    # Print final recent list
    print("\n" + "=" * 80)
    print("RECENT DIAGRAMS (Final State)")
    print("=" * 80)
    for i, d in enumerate(recent_diagrams, 1):
        print(f"{i}. {d['title']} (accessed: {d['last_accessed_at']})")
    
    return True


if __name__ == "__main__":
    print("\n")
    success = test_recent_diagrams()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    if success:
        print("✓ PASS: All tests passed")
        print("✓ Feature #153 (Recent Diagrams) is working correctly")
        sys.exit(0)
    else:
        print("❌ FAIL: Some tests failed")
        sys.exit(1)
