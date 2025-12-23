#!/usr/bin/env python3
"""
Test script for Feature #128: Delete diagram soft deletes to trash

This script tests the soft delete functionality for diagrams:
1. Create a test user and diagram
2. Soft delete the diagram (move to trash)
3. Verify diagram is removed from active list
4. Verify deleted diagram returns 404
5. Verify double-delete returns 404
6. Verify update on deleted diagram returns 404
"""

import requests
import json
from datetime import datetime
import sys


def test_soft_delete():
    """Test soft delete functionality."""
    
    # Create a test user and login
    test_email = f"delete_test_{datetime.now().timestamp()}@example.com"
    register_data = {
        "email": test_email,
        "password": "Test123!@#",
        "full_name": "Delete Test User"
    }
    
    print("=== Testing Feature #128: Soft Delete to Trash ===\n")
    
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
        "title": "Test Diagram for Deletion",
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
    print(f"   Title: {diagram.get('title')}")
    print(f"   is_deleted: {diagram.get('is_deleted')}")
    
    # Verify diagram is in list
    print("\n3. Verifying diagram appears in list...")
    response = requests.get("http://localhost:8082/", headers=headers)
    if response.status_code != 200:
        print(f"   ❌ Failed to list diagrams: {response.text}")
        return False
    
    diagrams_list = response.json()
    diagram_count_before = len(diagrams_list.get('diagrams', []))
    print(f"   ✅ Found {diagram_count_before} diagrams")
    
    # Soft delete the diagram
    print("\n4. Soft deleting diagram (moving to trash)...")
    response = requests.delete(f"http://localhost:8082/{diagram_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   ❌ Failed to delete diagram: {response.text}")
        return False
    
    result = response.json()
    print(f"   ✅ {result.get('message')}")
    print(f"   Deleted at: {result.get('deleted_at')}")
    
    # Verify diagram is not in active list anymore
    print("\n5. Verifying diagram is removed from active list...")
    response = requests.get("http://localhost:8082/", headers=headers)
    if response.status_code != 200:
        print(f"   ❌ Failed to list diagrams: {response.text}")
        return False
    
    diagrams_list = response.json()
    diagram_count_after = len(diagrams_list.get('diagrams', []))
    print(f"   ✅ Now showing {diagram_count_after} diagrams (was {diagram_count_before})")
    
    if diagram_count_after >= diagram_count_before:
        print("   ❌ Diagram still in active list!")
        return False
    
    print("   ✅ Diagram successfully removed from active list")
    
    # Try to get the deleted diagram
    print("\n6. Verifying deleted diagram returns 404...")
    response = requests.get(f"http://localhost:8082/{diagram_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    
    print("   ✅ Deleted diagram correctly returns 404")
    
    # Try to delete again (should fail)
    print("\n7. Verifying double-delete returns 404...")
    response = requests.delete(f"http://localhost:8082/{diagram_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    
    print("   ✅ Double-delete correctly returns 404")
    
    # Try to update deleted diagram (should fail)
    print("\n8. Verifying update on deleted diagram returns 404...")
    update_data = {
        "title": "Updated Title"
    }
    response = requests.put(f"http://localhost:8082/{diagram_id}", json=update_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 404:
        print(f"   ❌ Expected 404, got {response.status_code}")
        return False
    
    print("   ✅ Update on deleted diagram correctly returns 404")
    
    # Test unauthorized delete
    print("\n9. Testing unauthorized delete (different user)...")
    
    # Create another user
    test_email2 = f"delete_test2_{datetime.now().timestamp()}@example.com"
    register_data2 = {
        "email": test_email2,
        "password": "Test123!@#",
        "full_name": "Delete Test User 2"
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
    
    # Create a diagram as first user
    diagram_data2 = {
        "title": "Another Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": []},
        "note_content": ""
    }
    response = requests.post("http://localhost:8082/", json=diagram_data2, headers=headers)
    diagram_id2 = response.json().get('id')
    
    # Try to delete as second user (should fail)
    response = requests.delete(f"http://localhost:8082/{diagram_id2}", headers=headers2)
    print(f"   Status: {response.status_code}")
    if response.status_code != 403:
        print(f"   ❌ Expected 403, got {response.status_code}")
        return False
    
    print("   ✅ Unauthorized delete correctly returns 403")
    
    print("\n" + "="*60)
    print("✅ Feature #128 - Soft Delete to Trash - ALL TESTS PASSED!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_soft_delete()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
