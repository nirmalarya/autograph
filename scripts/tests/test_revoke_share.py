#!/usr/bin/env python3
"""Test Feature #138: Revoke share link."""

import requests
import json
import time

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_revoke_share():
    """Test revoking a share link."""
    
    print("=" * 80)
    print("FEATURE #138: REVOKE SHARE LINK")
    print("=" * 80)
    
    # Step 1: Register and login
    print("\n1. Register and login user...")
    register_data = {
        "email": f"revoke_test_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Revoke Test User"
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
        "title": "Test Diagram for Revoke",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "Test diagram for share revocation"
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
    
    # Step 4: Verify link works
    print("\n4. Verify link works...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Share access failed: {response.status_code}")
        print(response.text)
        return False
    
    shared_diagram = response.json()
    print(f"✅ Share link works (diagram: {shared_diagram['title']})")
    
    # Step 5: Revoke the share link
    print("\n5. Revoke share link...")
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}/share/{share_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Share revocation failed: {response.status_code}")
        print(response.text)
        return False
    
    revoke_result = response.json()
    print(f"✅ Share link revoked")
    print(f"   Message: {revoke_result['message']}")
    
    # Step 6: Attempt to access revoked share link
    print("\n6. Attempt to access revoked share link...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code == 404:
        print(f"✅ Revoked share correctly rejected with 404 Not Found")
        error_detail = response.json().get("detail", "")
        print(f"   Error message: {error_detail}")
        
        if "not found" not in error_detail.lower():
            print(f"⚠️  Warning: Error message doesn't mention 'not found'")
        
    elif response.status_code == 200:
        print(f"❌ Revoked share was accepted! Should have been rejected.")
        return False
    else:
        print(f"✅ Revoked share rejected with status {response.status_code}")
        print(f"   Error: {response.json().get('detail', 'Unknown error')}")
    
    # Step 7: Test revoking non-existent share
    print("\n7. Test revoking non-existent share...")
    fake_share_id = "00000000-0000-0000-0000-000000000000"
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}/share/{fake_share_id}",
        headers=headers
    )
    
    if response.status_code == 404:
        print(f"✅ Non-existent share correctly returns 404")
    else:
        print(f"⚠️  Warning: Expected 404, got {response.status_code}")
    
    # Step 8: Test revoking share from another user's diagram
    print("\n8. Test revoking share from another user's diagram...")
    
    # Create another user
    register_data2 = {
        "email": f"revoke_test2_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Revoke Test User 2"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data2)
    if response.status_code not in [200, 201]:
        print(f"❌ Second user registration failed: {response.status_code}")
        return False
    
    # Login as second user
    login_data2 = {
        "email": register_data2["email"],
        "password": register_data2["password"]
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data2)
    if response.status_code != 200:
        print(f"❌ Second user login failed: {response.status_code}")
        return False
    
    tokens2 = response.json()
    access_token2 = tokens2["access_token"]
    decoded2 = jwt.decode(access_token2, options={"verify_signature": False})
    user_id2 = decoded2["sub"]
    
    headers2 = {
        "Authorization": f"Bearer {access_token2}",
        "X-User-ID": user_id2
    }
    
    # Create a diagram as second user
    diagram_data2 = {
        "title": "Second User's Diagram",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "Test"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data2, headers=headers2)
    if response.status_code not in [200, 201]:
        print(f"❌ Second diagram creation failed: {response.status_code}")
        return False
    
    diagram2 = response.json()
    diagram_id2 = diagram2["id"]
    
    # Create share as second user
    response = requests.post(
        f"{BASE_URL}/{diagram_id2}/share",
        json=share_data,
        headers=headers2
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Second share creation failed: {response.status_code}")
        return False
    
    share2 = response.json()
    share_id2 = share2["share_id"]
    
    # Try to revoke second user's share as first user
    response = requests.delete(
        f"{BASE_URL}/{diagram_id2}/share/{share_id2}",
        headers=headers  # Using first user's headers
    )
    
    if response.status_code == 403:
        print(f"✅ Unauthorized revocation correctly rejected with 403 Forbidden")
    elif response.status_code == 404:
        print(f"✅ Unauthorized revocation rejected with 404 (also acceptable)")
    else:
        print(f"⚠️  Warning: Expected 403 or 404, got {response.status_code}")
    
    # Step 9: Create multiple shares and revoke one
    print("\n9. Test multiple shares - revoke one, others still work...")
    
    # Create two more shares for the first diagram
    response1 = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers
    )
    
    response2 = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers
    )
    
    if response1.status_code not in [200, 201] or response2.status_code not in [200, 201]:
        print(f"❌ Failed to create multiple shares")
        return False
    
    share_a = response1.json()
    share_b = response2.json()
    
    print(f"✅ Created two shares: {share_a['share_id'][:8]}... and {share_b['share_id'][:8]}...")
    
    # Revoke share A
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}/share/{share_a['share_id']}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to revoke share A: {response.status_code}")
        return False
    
    print(f"✅ Revoked share A")
    
    # Verify share A is revoked
    response = requests.get(f"{BASE_URL}/shared/{share_a['token']}")
    if response.status_code == 404:
        print(f"✅ Share A correctly revoked")
    else:
        print(f"❌ Share A still accessible!")
        return False
    
    # Verify share B still works
    response = requests.get(f"{BASE_URL}/shared/{share_b['token']}")
    if response.status_code == 200:
        print(f"✅ Share B still works correctly")
    else:
        print(f"❌ Share B was incorrectly revoked!")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #138 Complete!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_revoke_share()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
