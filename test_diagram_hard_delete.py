#!/usr/bin/env python3
"""
Test script for Feature #129: Delete diagram hard deletes permanently

This script tests the hard delete (permanent deletion) functionality:
1. Create a test user and diagram
2. Soft delete the diagram (move to trash)
3. Hard delete the diagram from trash (permanent)
4. Verify diagram is completely removed from database
5. Verify all versions are deleted
6. Verify hard delete only works on trashed diagrams
"""

import requests
import json
from datetime import datetime
import sys


def test_hard_delete():
    """Test hard delete functionality."""
    
    # Create a test user and login
    test_email = f"hard_delete_test_{datetime.now().timestamp()}@example.com"
    register_data = {
        "email": test_email,
        "password": "Test123!@#",
        "full_name": "Hard Delete Test User"
    }
    
    print("=== Testing Feature #129: Hard Delete (Permanent) ===\n")
    
    print("1. Creating test user...")
    response = requests.post("http://localhost:8085/register", json=register_data)
    if response.status_code != 201:
        print(f"   ❌ Failed to create user: {response.text}")
        return False
    
    user_id = response.json().get('id')
    print(f"   ✅ User created: {user_id}")
    
    # Login to get token
    login_data = {
        "email": test_email,
        "password": "Test123!@#"
    }
    response = requests.post("http://localhost:8085/login", json=login_data)
    if response.status_code != 200:
        print(f"   ❌ Failed to login: {response.text}")
        return False
    
    access_token = response.json().get('access_token')
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }
    
    # Create a diagram
    print("\n2. Creating test diagram...")
    diagram_data = {
        "title": "Test Diagram for Hard Delete",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"type": "rectangle"}]},
        "note_content": ""
    }
    
    response = requests.post("http://localhost:8082/", json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"   ❌ Failed to create diagram: {response.text}")
        return False
    
    diagram = response.json()
    diagram_id = diagram.get('id')
    print(f"   ✅ Diagram created: {diagram_id}")
    
    # Update diagram to create a version
    print("\n3. Updating diagram to create version history...")
    update_data = {
        "title": "Updated Title"
    }
    response = requests.put(f"http://localhost:8082/{diagram_id}", json=update_data, headers=headers)
    if response.status_code != 200:
        print(f"   ❌ Failed to update diagram: {response.text}")
        return False
    print("   ✅ Diagram updated (version 2 created)")
    
    # Verify versions exist
    response = requests.get(f"http://localhost:8082/{diagram_id}/versions", headers=headers)
    if response.status_code == 200:
        versions = response.json()
        print(f"   ✅ Found {len(versions)} versions")
    
    # Soft delete first
    print("\n4. Soft deleting diagram (moving to trash)...")
    response = requests.delete(f"http://localhost:8082/{diagram_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   ❌ Failed to soft delete: {response.text}")
        return False
    print("   ✅ Diagram moved to trash")
    
    # Try to hard delete active diagram (should fail)
    print("\n5. Verifying hard delete only works on trashed diagrams...")
    diagram_data2 = {
        "title": "Active Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": []},
        "note_content": ""
    }
    response = requests.post("http://localhost:8082/", json=diagram_data2, headers=headers)
    active_diagram_id = response.json().get('id')
    
    response = requests.delete(f"http://localhost:8082/{active_diagram_id}?permanent=true", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    print("   ✅ Hard delete on active diagram correctly returns 404")
    
    # Now hard delete the diagram from trash
    print("\n6. Hard deleting diagram from trash (permanent delete)...")
    response = requests.delete(f"http://localhost:8082/{diagram_id}?permanent=true", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   ❌ Failed to hard delete: {response.text}")
        return False
    
    result = response.json()
    print(f"   ✅ {result.get('message')}")
    print(f"   Versions deleted: {result.get('versions_deleted')}")
    
    if result.get('versions_deleted', 0) < 1:
        print("   ❌ No versions were deleted!")
        return False
    
    # Try to hard delete again (should fail)
    print("\n7. Verifying double hard-delete returns 404...")
    response = requests.delete(f"http://localhost:8082/{diagram_id}?permanent=true", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    print("   ✅ Double hard-delete correctly returns 404")
    
    # Try to get the hard-deleted diagram
    print("\n8. Verifying hard-deleted diagram returns 404...")
    response = requests.get(f"http://localhost:8082/{diagram_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    print("   ✅ Hard-deleted diagram correctly returns 404")
    
    # Try to get versions of hard-deleted diagram
    print("\n9. Verifying versions of hard-deleted diagram return empty...")
    response = requests.get(f"http://localhost:8082/{diagram_id}/versions", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   ✅ Versions endpoint returns 404 (diagram not found)")
    elif response.status_code == 200:
        versions = response.json()
        if len(versions) == 0:
            print("   ✅ Versions list is empty")
        else:
            print(f"   ❌ Found {len(versions)} versions (should be 0)")
            return False
    
    # Test unauthorized hard delete
    print("\n10. Testing unauthorized hard delete...")
    
    # Create another user
    test_email2 = f"hard_delete_test2_{datetime.now().timestamp()}@example.com"
    register_data2 = {
        "email": test_email2,
        "password": "Test123!@#",
        "full_name": "Hard Delete Test User 2"
    }
    
    response = requests.post("http://localhost:8085/register", json=register_data2)
    user_id2 = response.json().get('id')
    
    # Login as second user
    login_data2 = {
        "email": test_email2,
        "password": "Test123!@#"
    }
    response = requests.post("http://localhost:8085/login", json=login_data2)
    access_token2 = response.json().get('access_token')
    
    headers2 = {
        "Authorization": f"Bearer {access_token2}",
        "X-User-ID": user_id2,
        "Content-Type": "application/json"
    }
    
    # Create and soft delete a diagram as first user
    diagram_data3 = {
        "title": "Another Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": []},
        "note_content": ""
    }
    response = requests.post("http://localhost:8082/", json=diagram_data3, headers=headers)
    diagram_id3 = response.json().get('id')
    
    # Soft delete
    requests.delete(f"http://localhost:8082/{diagram_id3}", headers=headers)
    
    # Try to hard delete as second user (should fail)
    response = requests.delete(f"http://localhost:8082/{diagram_id3}?permanent=true", headers=headers2)
    print(f"   Status: {response.status_code}")
    if response.status_code != 403:
        print(f"   ❌ Expected 403, got {response.status_code}")
        return False
    print("   ✅ Unauthorized hard delete correctly returns 403")
    
    print("\n" + "="*60)
    print("✅ Feature #129 - Hard Delete (Permanent) - ALL TESTS PASSED!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_hard_delete()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
