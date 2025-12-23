#!/usr/bin/env python3
"""Test Feature #107: Permission check - shared diagram with edit access."""

import requests
import json
import time
import jwt

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_share_edit_permission():
    """Test that users with edit share access can edit but not delete diagram."""
    
    print("=" * 80)
    print("FEATURE #107: PERMISSION CHECK - SHARED DIAGRAM EDIT ACCESS")
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
    
    # Step 2: Register User B (editor)
    print("\n2. Register User B (editor)...")
    user_b_email = f"editor_{int(time.time())}@example.com"
    register_data_b = {
        "email": user_b_email,
        "password": "SecurePass123!",
        "full_name": "User B (Editor)"
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
        "title": "Shared Diagram - Edit Access Test",
        "type": "canvas",
        "canvas_data": {"shapes": [{"type": "rectangle", "id": "1"}], "version": 1},
        "note_content": "Original content by User A"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers_a)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created by User A (id: {diagram_id})")
    
    # Step 4: User A shares diagram with edit permission
    print("\n4. User A shares diagram with edit permission...")
    share_data = {
        "permission": "edit",
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
    print(f"✅ Share link created with edit permission")
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
    
    # Verify permission is edit
    if shared_diagram['permission'] != "edit":
        print(f"❌ Expected permission 'edit', got '{shared_diagram['permission']}'")
        return False
    
    print("✅ Permission confirmed as 'edit'")
    
    # Step 6: User B edits diagram (should succeed)
    print("\n6. User B edits diagram...")
    update_data = {
        "title": "Modified by User B (Editor)",
        "canvas_data": {"shapes": [{"type": "circle", "id": "2"}], "version": 2},
        "note_content": "Content updated by User B"
    }
    
    # Add share token to headers
    headers_b_with_share = headers_b.copy()
    headers_b_with_share["X-Share-Token"] = share_token
    
    response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        json=update_data,
        headers=headers_b_with_share
    )
    
    # Verify 200 OK response
    if response.status_code != 200:
        print(f"❌ Expected 200 OK, got {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Received 200 OK response")
    
    updated = response.json()
    print(f"   Updated title: {updated['title']}")
    print(f"   Version: {updated['current_version']}")
    
    # Step 7: Verify changes were saved
    print("\n7. Verify changes were saved...")
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code != 200:
        print(f"❌ Failed to fetch diagram: {response.status_code}")
        print(response.text)
        return False
    
    current_diagram = response.json()
    
    if current_diagram["title"] != update_data["title"]:
        print(f"❌ Title not updated. Expected: '{update_data['title']}', Got: '{current_diagram['title']}'")
        return False
    
    if current_diagram["note_content"] != update_data["note_content"]:
        print(f"❌ Note content not updated")
        return False
    
    print("✅ Changes were saved successfully")
    print(f"   Title: {current_diagram['title']}")
    print(f"   Note: {current_diagram['note_content']}")
    print(f"   Version: {current_diagram['current_version']}")
    
    # Step 8: User B attempts to delete diagram (should fail)
    print("\n8. User B attempts to delete diagram...")
    
    # Try with share token
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}",
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
    print(f"✅ Error message: '{error_message}'")
    
    # Step 9: Verify diagram still exists (not deleted)
    print("\n9. Verify diagram still exists (not deleted)...")
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code != 200:
        print(f"❌ Diagram not found: {response.status_code}")
        print(response.text)
        return False
    
    diagram_check = response.json()
    if diagram_check.get("is_deleted", False):
        print("❌ Diagram was deleted despite permission check")
        return False
    
    print("✅ Diagram still exists (not deleted)")
    
    # Step 10: Verify owner can still delete
    print("\n10. Verify owner (User A) can delete...")
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}",
        headers=headers_a
    )
    
    if response.status_code != 200:
        print(f"❌ Owner cannot delete diagram: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Owner can delete diagram (200 OK)")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #107 Complete!")
    print("=" * 80)
    print("\nSummary:")
    print("  • User B with edit access can view diagram ✓")
    print("  • User B with edit access can edit diagram ✓")
    print("  • User B's changes are saved ✓")
    print("  • User B with edit access CANNOT delete diagram ✓")
    print("  • Only owner can delete diagram ✓")
    
    return True


if __name__ == "__main__":
    try:
        success = test_share_edit_permission()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
