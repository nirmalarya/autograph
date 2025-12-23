#!/usr/bin/env python3
"""
Test Feature #130: Restore diagram from trash

This test verifies that diagrams can be restored from trash.
"""

import requests
import uuid
import json
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def test_restore_diagram():
    """Test restoring a diagram from trash."""
    print_section("Testing Feature #130: Restore Diagram from Trash")
    
    # Step 1: Create test user
    print("\n1. Creating test user...")
    user_email = f"test-restore-{uuid.uuid4()}@example.com"
    user_password = "SecurePass123!"
    
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": user_email,
            "password": user_password
        }
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"   ❌ Failed to create user: {register_response.status_code}")
        print(f"   Response: {register_response.text}")
        return False
    
    # Register returns user data directly, need to login to get token
    user_data = register_response.json()
    user_id = user_data["id"]
    
    # Login to get access token
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": user_email,
            "password": user_password
        }
    )
    
    if login_response.status_code != 200:
        print(f"   ❌ Failed to login: {login_response.status_code}")
        return False
    
    login_data = login_response.json()
    access_token = login_data["access_token"]
    
    print(f"   ✅ User created: {user_id}")
    
    # Step 2: Create test diagram
    print("\n2. Creating test diagram...")
    diagram_data = {
        "title": "Test Diagram for Restore",
        "file_type": "canvas",
        "canvas_data": {"elements": [{"type": "rectangle", "id": "rect1"}]},
        "note_content": ""
    }
    
    create_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        json=diagram_data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    if create_response.status_code != 200:
        print(f"   ❌ Failed to create diagram: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return False
    
    diagram = create_response.json()
    diagram_id = diagram["id"]
    
    print(f"   ✅ Diagram created: {diagram_id}")
    print(f"   Title: {diagram['title']}")
    print(f"   is_deleted: {diagram.get('is_deleted', False)}")
    
    # Step 3: Verify diagram appears in list
    print("\n3. Verifying diagram appears in active list...")
    list_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    list_data = list_response.json()
    diagrams_before = list_data.get('diagrams', [])
    print(f"   ✅ Found {len(diagrams_before)} active diagrams")
    
    # Step 4: Soft delete diagram (move to trash)
    print("\n4. Soft deleting diagram (moving to trash)...")
    delete_response = requests.delete(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {delete_response.status_code}")
    if delete_response.status_code != 200:
        print(f"   ❌ Failed to delete diagram: {delete_response.text}")
        return False
    
    delete_data = delete_response.json()
    print(f"   ✅ Diagram moved to trash")
    print(f"   Deleted at: {delete_data.get('deleted_at')}")
    
    # Step 5: Verify diagram is removed from active list
    print("\n5. Verifying diagram is removed from active list...")
    list_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    list_data = list_response.json()
    diagrams_after_delete = list_data.get('diagrams', [])
    print(f"   ✅ Now showing {len(diagrams_after_delete)} active diagrams")
    
    # Check if the deleted diagram is in the list
    deleted_diagram_in_list = any(d['id'] == diagram_id for d in diagrams_after_delete)
    
    if deleted_diagram_in_list:
        print(f"   ❌ Deleted diagram still appears in active list")
        return False
    else:
        print(f"   ✅ Diagram successfully removed from active list")
    
    # Step 6: Verify deleted diagram returns 404 on GET
    print("\n6. Verifying deleted diagram returns 404...")
    get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {get_response.status_code}")
    if get_response.status_code == 404:
        print(f"   ✅ Deleted diagram correctly returns 404")
    else:
        print(f"   ❌ Expected 404, got {get_response.status_code}")
        return False
    
    # Step 7: Restore diagram from trash
    print("\n7. Restoring diagram from trash...")
    restore_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/restore",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {restore_response.status_code}")
    if restore_response.status_code != 200:
        print(f"   ❌ Failed to restore diagram: {restore_response.text}")
        return False
    
    restore_data = restore_response.json()
    print(f"   ✅ Diagram restored from trash")
    print(f"   Message: {restore_data.get('message')}")
    print(f"   Title: {restore_data.get('title')}")
    print(f"   Restored at: {restore_data.get('restored_at')}")
    
    # Step 8: Verify diagram is back in active list
    print("\n8. Verifying diagram is back in active list...")
    list_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    list_data = list_response.json()
    diagrams_after_restore = list_data.get('diagrams', [])
    print(f"   ✅ Now showing {len(diagrams_after_restore)} active diagrams")
    
    # Verify the restored diagram is in the list
    restored_diagram = next((d for d in diagrams_after_restore if d['id'] == diagram_id), None)
    if restored_diagram:
        print(f"   ✅ Restored diagram found in list")
        print(f"   Title: {restored_diagram['title']}")
        print(f"   ✅ Diagram successfully restored to active list")
    else:
        print(f"   ❌ Restored diagram not found in list")
        return False
    
    # Step 9: Verify diagram is accessible again
    print("\n9. Verifying diagram is accessible again...")
    get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {get_response.status_code}")
    if get_response.status_code == 200:
        diagram_data = get_response.json()
        print(f"   ✅ Diagram is accessible")
        print(f"   Title: {diagram_data['title']}")
        print(f"   is_deleted: {diagram_data.get('is_deleted', False)}")
        
        if diagram_data.get('is_deleted', False):
            print(f"   ❌ Diagram still marked as deleted")
            return False
        else:
            print(f"   ✅ Diagram is_deleted flag is False")
    else:
        print(f"   ❌ Expected 200, got {get_response.status_code}")
        return False
    
    # Step 10: Test restoring non-existent diagram
    print("\n10. Testing restore of non-existent diagram...")
    fake_id = str(uuid.uuid4())
    restore_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{fake_id}/restore",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {restore_response.status_code}")
    if restore_response.status_code == 404:
        print(f"   ✅ Non-existent diagram correctly returns 404")
    else:
        print(f"   ❌ Expected 404, got {restore_response.status_code}")
        return False
    
    # Step 11: Test unauthorized restore
    print("\n11. Testing unauthorized restore (different user)...")
    
    # Create another user
    other_email = f"test-other-{uuid.uuid4()}@example.com"
    other_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": other_email,
            "password": user_password
        }
    )
    
    other_user = other_response.json()
    other_user_id = other_user["id"]
    
    # Login to get token
    other_login = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": other_email,
            "password": user_password
        }
    )
    other_token = other_login.json()["access_token"]
    
    # Create and delete a diagram with the original user
    create_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        json={
            "title": "Test Diagram for Unauthorized Restore",
            "file_type": "canvas",
            "canvas_data": {},
            "note_content": ""
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    test_diagram_id = create_response.json()["id"]
    
    # Delete it
    requests.delete(
        f"{DIAGRAM_SERVICE_URL}/{test_diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    # Try to restore with different user
    restore_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{test_diagram_id}/restore",
        headers={
            "Authorization": f"Bearer {other_token}",
            "X-User-ID": other_user_id
        }
    )
    
    print(f"   Status: {restore_response.status_code}")
    if restore_response.status_code == 403:
        print(f"   ✅ Unauthorized restore correctly returns 403")
    else:
        print(f"   ❌ Expected 403, got {restore_response.status_code}")
        return False
    
    # Step 12: Test restoring already active diagram
    print("\n12. Testing restore of already active diagram...")
    restore_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/restore",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {restore_response.status_code}")
    if restore_response.status_code == 404:
        print(f"   ✅ Active diagram correctly returns 404 (not in trash)")
    else:
        print(f"   ❌ Expected 404, got {restore_response.status_code}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_restore_diagram()
        
        if success:
            print_section("✅ Feature #130 - Restore from Trash - ALL TESTS PASSED!")
        else:
            print_section("❌ Feature #130 - Restore from Trash - TESTS FAILED!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
