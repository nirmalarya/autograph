#!/usr/bin/env python3
"""
Test Feature #132: Duplicate diagram creates copy with new UUID

This test verifies that diagrams can be duplicated with a new UUID and fresh version history.
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

def test_duplicate_diagram():
    """Test duplicating a diagram."""
    print_section("Testing Feature #132: Duplicate Diagram")
    
    # Step 1: Create test user
    print("\n1. Creating test user...")
    user_email = f"test-duplicate-{uuid.uuid4()}@example.com"
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
    
    # Step 2: Create original diagram with title 'Original'
    print("\n2. Creating original diagram with title 'Original'...")
    diagram_data = {
        "title": "Original",
        "file_type": "canvas",
        "canvas_data": {
            "elements": [
                {"type": "rectangle", "id": "rect1", "x": 10, "y": 10},
                {"type": "circle", "id": "circle1", "x": 100, "y": 100}
            ]
        },
        "note_content": "This is the original diagram"
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
    
    original = create_response.json()
    original_id = original["id"]
    
    print(f"   ✅ Original diagram created: {original_id}")
    print(f"   Title: {original['title']}")
    print(f"   Canvas elements: {len(original['canvas_data']['elements'])}")
    
    # Step 3: Duplicate the diagram
    print("\n3. Duplicating the diagram...")
    duplicate_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{original_id}/duplicate",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {duplicate_response.status_code}")
    if duplicate_response.status_code != 200:
        print(f"   ❌ Failed to duplicate diagram: {duplicate_response.text}")
        return False
    
    duplicate_data = duplicate_response.json()
    duplicate_id = duplicate_data["duplicate_id"]
    
    print(f"   ✅ Diagram duplicated successfully")
    print(f"   Original ID: {duplicate_data['original_id']}")
    print(f"   Duplicate ID: {duplicate_id}")
    print(f"   Title: {duplicate_data['title']}")
    
    # Step 4: Verify new diagram has different UUID
    print("\n4. Verifying new diagram has different UUID...")
    if duplicate_id != original_id:
        print(f"   ✅ Duplicate has different UUID")
        print(f"   Original: {original_id}")
        print(f"   Duplicate: {duplicate_id}")
    else:
        print(f"   ❌ Duplicate has same UUID as original")
        return False
    
    # Step 5: Verify new diagram title is 'Original (Copy)'
    print("\n5. Verifying new diagram title...")
    if duplicate_data['title'] == "Original (Copy)":
        print(f"   ✅ Title correctly set to 'Original (Copy)'")
    else:
        print(f"   ❌ Expected 'Original (Copy)', got '{duplicate_data['title']}'")
        return False
    
    # Step 6: Get duplicate diagram and verify canvas_data copied exactly
    print("\n6. Verifying canvas_data copied exactly...")
    get_duplicate_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{duplicate_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    if get_duplicate_response.status_code != 200:
        print(f"   ❌ Failed to get duplicate: {get_duplicate_response.status_code}")
        return False
    
    duplicate_full = get_duplicate_response.json()
    
    # Compare canvas_data
    if duplicate_full['canvas_data'] == original['canvas_data']:
        print(f"   ✅ Canvas data copied exactly")
        print(f"   Elements in duplicate: {len(duplicate_full['canvas_data']['elements'])}")
    else:
        print(f"   ❌ Canvas data does not match")
        return False
    
    # Compare note_content
    if duplicate_full['note_content'] == original['note_content']:
        print(f"   ✅ Note content copied exactly")
    else:
        print(f"   ❌ Note content does not match")
        return False
    
    # Step 7: Verify new diagram has fresh version history (version 1)
    print("\n7. Verifying new diagram has fresh version history...")
    current_version = duplicate_full.get('current_version', duplicate_full.get('version', 0))
    if current_version == 1:
        print(f"   ✅ Duplicate has version 1 (fresh version history)")
    else:
        print(f"   ❌ Expected version 1, got version {current_version}")
        return False
    
    # Get versions for duplicate
    versions_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{duplicate_id}/versions",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    if versions_response.status_code == 200:
        versions = versions_response.json()
        print(f"   ✅ Duplicate has {len(versions)} version(s)")
        if len(versions) == 1:
            print(f"   ✅ Fresh version history confirmed")
        else:
            print(f"   ⚠️  Expected 1 version, got {len(versions)}")
    
    # Step 8: Verify original diagram unchanged
    print("\n8. Verifying original diagram unchanged...")
    get_original_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{original_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    if get_original_response.status_code != 200:
        print(f"   ❌ Failed to get original: {get_original_response.status_code}")
        return False
    
    original_after = get_original_response.json()
    
    if original_after['title'] == original['title']:
        print(f"   ✅ Original title unchanged: '{original_after['title']}'")
    else:
        print(f"   ❌ Original title changed")
        return False
    
    if original_after['id'] == original['id']:
        print(f"   ✅ Original ID unchanged: {original_after['id']}")
    else:
        print(f"   ❌ Original ID changed")
        return False
    
    # Step 9: Test duplicating non-existent diagram
    print("\n9. Testing duplicate of non-existent diagram...")
    fake_id = str(uuid.uuid4())
    duplicate_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{fake_id}/duplicate",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    print(f"   Status: {duplicate_response.status_code}")
    if duplicate_response.status_code == 404:
        print(f"   ✅ Non-existent diagram correctly returns 404")
    else:
        print(f"   ❌ Expected 404, got {duplicate_response.status_code}")
        return False
    
    # Step 10: Test unauthorized duplicate
    print("\n10. Testing unauthorized duplicate (different user)...")
    
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
    
    # Try to duplicate with different user
    duplicate_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{original_id}/duplicate",
        headers={
            "Authorization": f"Bearer {other_token}",
            "X-User-ID": other_user_id
        }
    )
    
    print(f"   Status: {duplicate_response.status_code}")
    if duplicate_response.status_code == 403:
        print(f"   ✅ Unauthorized duplicate correctly returns 403")
    else:
        print(f"   ❌ Expected 403, got {duplicate_response.status_code}")
        return False
    
    # Step 11: Test duplicating a duplicate (should append another (Copy))
    print("\n11. Testing duplicate of duplicate...")
    duplicate2_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{duplicate_id}/duplicate",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    if duplicate2_response.status_code == 200:
        duplicate2_data = duplicate2_response.json()
        print(f"   ✅ Duplicate of duplicate created")
        print(f"   Title: {duplicate2_data['title']}")
        
        # Title should be "Original (Copy) (Copy)"
        if duplicate2_data['title'] == "Original (Copy) (Copy)":
            print(f"   ✅ Title correctly appended (Copy)")
        else:
            print(f"   ⚠️  Title: {duplicate2_data['title']}")
    else:
        print(f"   ❌ Failed to duplicate duplicate: {duplicate2_response.status_code}")
        return False
    
    # Step 12: Verify both diagrams in list
    print("\n12. Verifying all diagrams appear in list...")
    list_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )
    
    list_data = list_response.json()
    diagrams = list_data.get('diagrams', [])
    
    print(f"   ✅ Found {len(diagrams)} diagrams")
    
    # Find our diagrams
    original_in_list = any(d['id'] == original_id for d in diagrams)
    duplicate_in_list = any(d['id'] == duplicate_id for d in diagrams)
    
    if original_in_list and duplicate_in_list:
        print(f"   ✅ Both original and duplicate appear in list")
    else:
        print(f"   ❌ Missing diagrams in list")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_duplicate_diagram()
        
        if success:
            print_section("✅ Feature #132 - Duplicate Diagram - ALL TESTS PASSED!")
        else:
            print_section("❌ Feature #132 - Duplicate Diagram - TESTS FAILED!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
