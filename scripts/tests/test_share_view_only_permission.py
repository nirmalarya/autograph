#!/usr/bin/env python3
"""Test Feature #106: Permission check - shared diagram with view-only access."""

import requests
import json
import time
import jwt

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_share_view_only_permission():
    """Test that users with view-only share access cannot edit diagram."""
    
    print("=" * 80)
    print("FEATURE #106: PERMISSION CHECK - SHARED DIAGRAM VIEW-ONLY ACCESS")
    print("=" * 80)
    
    # Step 1: Register User A (diagram owner)
    print("\n1. Register User A (diagram owner)...")
    user_a_email = f"owner_{int(time.time())}@example.com"
    register_data_a = {
        "email": user_a_email,
        "password": "SecurePass123!",
        "full_name": "User A (Owner)"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data_a)
    if response.status_code not in [200, 201]:
        print(f"❌ User A registration failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User A registered")
    
    # Login User A
    login_data_a = {
        "email": user_a_email,
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data_a)
    if response.status_code != 200:
        print(f"❌ User A login failed: {response.status_code}")
        print(response.text)
        return False
    
    tokens_a = response.json()
    access_token_a = tokens_a["access_token"]
    
    # Decode JWT to get user_id
    decoded_a = jwt.decode(access_token_a, options={"verify_signature": False})
    user_id_a = decoded_a["sub"]
    print(f"✅ User A logged in (user_id: {user_id_a})")
    
    headers_a = {
        "Authorization": f"Bearer {access_token_a}",
        "X-User-ID": user_id_a
    }
    
    # Step 2: Register User B (viewer)
    print("\n2. Register User B (viewer)...")
    user_b_email = f"viewer_{int(time.time())}@example.com"
    register_data_b = {
        "email": user_b_email,
        "password": "SecurePass123!",
        "full_name": "User B (Viewer)"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data_b)
    if response.status_code not in [200, 201]:
        print(f"❌ User B registration failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User B registered")
    
    # Login User B
    login_data_b = {
        "email": user_b_email,
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data_b)
    if response.status_code != 200:
        print(f"❌ User B login failed: {response.status_code}")
        print(response.text)
        return False
    
    tokens_b = response.json()
    access_token_b = tokens_b["access_token"]
    
    # Decode JWT to get user_id
    decoded_b = jwt.decode(access_token_b, options={"verify_signature": False})
    user_id_b = decoded_b["sub"]
    print(f"✅ User B logged in (user_id: {user_id_b})")
    
    headers_b = {
        "Authorization": f"Bearer {access_token_b}",
        "X-User-ID": user_id_b
    }
    
    # Step 3: User A creates diagram
    print("\n3. User A creates diagram...")
    diagram_data = {
        "title": "Shared Diagram - View Only Test",
        "type": "canvas",
        "canvas_data": {"shapes": [{"type": "rectangle", "id": "1"}], "version": 1},
        "note_content": "Original content"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers_a)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created by User A (id: {diagram_id})")
    
    # Step 4: User A shares diagram with view-only permission
    print("\n4. User A shares diagram with view-only permission...")
    share_data = {
        "permission": "view",
        "is_public": True
    }
    
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers_a
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Share creation failed: {response.status_code}")
        print(response.text)
        return False
    
    share = response.json()
    share_token = share["token"]
    print(f"✅ Share link created with view-only permission")
    print(f"   Token: {share_token[:20]}...")
    print(f"   Permission: {share['permission']}")
    
    # Step 5: User B accesses diagram via share link
    print("\n5. User B accesses diagram via share link...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Failed to access shared diagram: {response.status_code}")
        print(response.text)
        return False
    
    shared_diagram = response.json()
    print("✅ User B can view diagram")
    print(f"   Title: {shared_diagram['title']}")
    print(f"   Permission: {shared_diagram['permission']}")
    
    # Verify permission is view-only
    if shared_diagram['permission'] != "view":
        print(f"❌ Expected permission 'view', got '{shared_diagram['permission']}'")
        return False
    
    print("✅ Permission confirmed as 'view'")
    
    # Step 6: User B attempts to edit diagram (should fail)
    print("\n6. User B attempts to edit diagram...")
    update_data = {
        "title": "Modified by User B",
        "canvas_data": {"shapes": [{"type": "circle", "id": "2"}], "version": 2}
    }
    
    # Add share token to headers
    headers_b_with_share = headers_b.copy()
    headers_b_with_share["X-Share-Token"] = share_token
    
    response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        json=update_data,
        headers=headers_b_with_share
    )
    
    # Verify 403 Forbidden response
    if response.status_code != 403:
        print(f"❌ Expected 403 Forbidden, got {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Received 403 Forbidden response")
    
    # Verify error message
    error_data = response.json()
    if "detail" not in error_data:
        print("❌ No 'detail' field in error response")
        print(response.text)
        return False
    
    error_message = error_data["detail"]
    expected_phrases = [
        "view-only access",
        "view only",
        "cannot edit",
        "permission"
    ]
    
    message_found = any(phrase.lower() in error_message.lower() for phrase in expected_phrases)
    if not message_found:
        print(f"❌ Error message doesn't indicate view-only restriction: {error_message}")
        return False
    
    print(f"✅ Error message indicates view-only restriction: '{error_message}'")
    
    # Step 7: Verify diagram was not modified
    print("\n7. Verify diagram was not modified...")
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code != 200:
        print(f"❌ Failed to fetch diagram: {response.status_code}")
        print(response.text)
        return False
    
    current_diagram = response.json()
    
    if current_diagram["title"] != diagram_data["title"]:
        print(f"❌ Diagram title was modified: '{current_diagram['title']}'")
        return False
    
    print("✅ Diagram was not modified")
    print(f"   Title still: {current_diagram['title']}")
    
    # Step 8: Test that User B cannot edit without share token either
    print("\n8. Test User B cannot edit without share token...")
    response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        json=update_data,
        headers=headers_b  # Without X-Share-Token
    )
    
    if response.status_code != 403:
        print(f"❌ Expected 403 Forbidden without share token, got {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User B cannot edit without share token (403 Forbidden)")
    
    # Step 9: Verify owner can still edit
    print("\n9. Verify owner (User A) can still edit...")
    owner_update = {
        "title": "Updated by Owner",
        "canvas_data": {"shapes": [{"type": "triangle", "id": "3"}], "version": 2}
    }
    
    response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        json=owner_update,
        headers=headers_a
    )
    
    if response.status_code != 200:
        print(f"❌ Owner cannot edit diagram: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Owner can edit diagram (200 OK)")
    
    # Verify update was applied
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    updated_diagram = response.json()
    
    if updated_diagram["title"] != owner_update["title"]:
        print(f"❌ Owner's update not applied")
        return False
    
    print(f"✅ Owner's update applied: '{updated_diagram['title']}'")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #106 Complete!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_share_view_only_permission()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
