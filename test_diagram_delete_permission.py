#!/usr/bin/env python3
"""Test Feature #105: Permission check - only diagram owner can delete diagram."""

import requests
import json
import time
import jwt

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_diagram_delete_permission():
    """Test that only diagram owner can delete diagram."""
    
    print("=" * 80)
    print("FEATURE #105: PERMISSION CHECK - ONLY OWNER CAN DELETE DIAGRAM")
    print("=" * 80)
    
    # Step 1: Register User A
    print("\n1. Register User A...")
    user_a_email = f"user_a_{int(time.time())}@example.com"
    register_data_a = {
        "email": user_a_email,
        "password": "SecurePass123!",
        "full_name": "User A"
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
    
    # Step 2: Register User B
    print("\n2. Register User B...")
    user_b_email = f"user_b_{int(time.time())}@example.com"
    register_data_b = {
        "email": user_b_email,
        "password": "SecurePass123!",
        "full_name": "User B"
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
        "title": "User A's Diagram",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "This diagram belongs to User A"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers_a)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created by User A (id: {diagram_id})")
    print(f"   Owner: {diagram['owner_id']}")
    
    # Step 4: User B attempts to delete User A's diagram
    print("\n4. User B attempts to delete User A's diagram...")
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}",
        headers=headers_b
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
    expected_messages = [
        "Not authorized to delete this diagram",
        "You do not have permission to delete this diagram",
        "permission",
        "authorized"
    ]
    
    message_found = any(msg.lower() in error_message.lower() for msg in expected_messages)
    if not message_found:
        print(f"❌ Error message doesn't indicate permission issue: {error_message}")
        return False
    
    print(f"✅ Error message indicates permission issue: '{error_message}'")
    
    # Step 5: Verify diagram still exists (not deleted)
    print("\n5. Verify diagram still exists...")
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code != 200:
        print(f"❌ Diagram fetch failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram_check = response.json()
    if diagram_check.get("is_deleted", False):
        print("❌ Diagram was deleted despite permission check")
        return False
    
    print("✅ Diagram still exists (not deleted)")
    
    # Step 6: User A deletes own diagram
    print("\n6. User A deletes own diagram...")
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}",
        headers=headers_a
    )
    
    # Verify 200 OK response
    if response.status_code != 200:
        print(f"❌ Expected 200 OK, got {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Received 200 OK response")
    
    # Step 7: Verify diagram moved to trash
    print("\n7. Verify diagram moved to trash...")
    delete_response = response.json()
    
    if "message" not in delete_response:
        print("❌ No 'message' field in delete response")
        print(response.text)
        return False
    
    message = delete_response["message"]
    if "trash" not in message.lower() and "deleted" not in message.lower():
        print(f"❌ Message doesn't indicate deletion: {message}")
        return False
    
    print(f"✅ Message confirms deletion: '{message}'")
    
    # Verify diagram is marked as deleted
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code == 200:
        diagram_check = response.json()
        if not diagram_check.get("is_deleted", False):
            print("❌ Diagram not marked as deleted")
            return False
        print("✅ Diagram marked as deleted (is_deleted=True)")
    elif response.status_code == 404:
        print("✅ Diagram not found in active diagrams (moved to trash)")
    else:
        print(f"⚠️  Unexpected status code when checking diagram: {response.status_code}")
    
    # Step 8: Test hard delete permission (from trash)
    print("\n8. Test hard delete permission (from trash)...")
    
    # User B attempts to permanently delete User A's diagram from trash
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}?permanent=true",
        headers=headers_b
    )
    
    if response.status_code != 403:
        print(f"❌ Expected 403 Forbidden for hard delete, got {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User B cannot hard delete User A's diagram (403 Forbidden)")
    
    # User A can permanently delete own diagram
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}?permanent=true",
        headers=headers_a
    )
    
    if response.status_code != 200:
        print(f"❌ User A cannot hard delete own diagram: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User A can hard delete own diagram (200 OK)")
    
    # Verify diagram is permanently deleted
    response = requests.get(f"{BASE_URL}/{diagram_id}", headers=headers_a)
    if response.status_code != 404:
        print(f"❌ Diagram should be permanently deleted (404), got {response.status_code}")
        return False
    
    print("✅ Diagram permanently deleted (404 Not Found)")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #105 Complete!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_diagram_delete_permission()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
