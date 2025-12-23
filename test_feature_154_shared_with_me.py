#!/usr/bin/env python3
"""
Test Feature #154: Shared with me view

Steps:
1. User A shares diagram with User B
2. User B logs in
3. Navigate to /dashboard
4. Click 'Shared with me' tab
5. Verify shared diagram appears
6. Verify owner shown as User A
7. Verify permission level shown (view/edit)
8. User A shares another diagram
9. Verify new diagram appears in list
"""

import requests
import json
import time

BASE_URL_AUTH = "http://localhost:8085"
BASE_URL_DIAGRAM = "http://localhost:8082"

def test_feature_154():
    """Test shared with me functionality."""
    
    print("=" * 80)
    print("FEATURE #154: SHARED WITH ME VIEW")
    print("=" * 80)
    
    # Step 1: Create User A and User B
    print("\n[Step 1] Creating test users...")
    
    timestamp = int(time.time())
    user_a_email = f"user_a_{timestamp}@example.com"
    user_b_email = f"user_b_{timestamp}@example.com"
    password = "TestPass123!"
    
    # Register User A
    response = requests.post(f"{BASE_URL_AUTH}/register", json={
        "email": user_a_email,
        "password": password
    })
    assert response.status_code == 201, f"User A registration failed: {response.text}"
    print(f"✓ User A registered: {user_a_email}")
    
    # Register User B
    response = requests.post(f"{BASE_URL_AUTH}/register", json={
        "email": user_b_email,
        "password": password
    })
    assert response.status_code == 201, f"User B registration failed: {response.text}"
    print(f"✓ User B registered: {user_b_email}")
    
    # Login User A
    response = requests.post(f"{BASE_URL_AUTH}/login", json={
        "email": user_a_email,
        "password": password
    })
    assert response.status_code == 200, f"User A login failed: {response.text}"
    user_a_data = response.json()
    user_a_token = user_a_data['access_token']
    
    # Decode JWT to get user ID
    import base64
    user_a_payload = json.loads(base64.b64decode(user_a_token.split('.')[1] + '=='))
    user_a_id = user_a_payload['sub']
    print(f"✓ User A logged in (ID: {user_a_id})")
    
    # Login User B
    response = requests.post(f"{BASE_URL_AUTH}/login", json={
        "email": user_b_email,
        "password": password
    })
    assert response.status_code == 200, f"User B login failed: {response.text}"
    user_b_data = response.json()
    user_b_token = user_b_data['access_token']
    
    # Decode JWT to get user ID
    user_b_payload = json.loads(base64.b64decode(user_b_token.split('.')[1] + '=='))
    user_b_id = user_b_payload['sub']
    print(f"✓ User B logged in (ID: {user_b_id})")
    
    # Step 2: User A creates a diagram
    print("\n[Step 2] User A creates a diagram...")
    
    response = requests.post(f"{BASE_URL_DIAGRAM}/", 
        headers={"X-User-ID": user_a_id},
        json={
            "title": "Test Diagram for Sharing",
            "file_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )
    assert response.status_code in [200, 201], f"Diagram creation failed: {response.status_code} - {response.text}"
    diagram_1 = response.json()
    diagram_1_id = diagram_1['id']
    print(f"✓ Diagram created (ID: {diagram_1_id})")
    
    # Step 3: User A shares diagram with User B (view permission)
    print("\n[Step 3] User A shares diagram with User B (view permission)...")
    
    response = requests.post(f"{BASE_URL_DIAGRAM}/{diagram_1_id}/share",
        headers={"X-User-ID": user_a_id},
        json={
            "shared_with_email": user_b_email,
            "permission": "view"
        }
    )
    assert response.status_code == 200, f"Share creation failed: {response.text}"
    share_1 = response.json()
    print(f"✓ Diagram shared with User B")
    print(f"  - Share ID: {share_1['share_id']}")
    print(f"  - Permission: {share_1['permission']}")
    if 'shared_with_email' in share_1:
        print(f"  - Shared with: {share_1['shared_with_email']}")
    
    # Step 4: User B checks "Shared with me" endpoint
    print("\n[Step 4] User B checks 'Shared with me' endpoint...")
    
    response = requests.get(f"{BASE_URL_DIAGRAM}/shared-with-me",
        headers={"X-User-ID": user_b_id}
    )
    assert response.status_code == 200, f"Shared with me request failed: {response.text}"
    shared_data = response.json()
    print(f"✓ Shared with me endpoint returned {shared_data['total']} diagram(s)")
    
    # Step 5: Verify shared diagram appears
    print("\n[Step 5] Verifying shared diagram appears...")
    
    assert shared_data['total'] == 1, f"Expected 1 shared diagram, got {shared_data['total']}"
    shared_diagram = shared_data['diagrams'][0]
    assert shared_diagram['id'] == diagram_1_id, "Diagram ID mismatch"
    assert shared_diagram['title'] == "Test Diagram for Sharing", "Diagram title mismatch"
    print(f"✓ Shared diagram found in list")
    print(f"  - Title: {shared_diagram['title']}")
    print(f"  - ID: {shared_diagram['id']}")
    
    # Step 6: Verify owner shown as User A
    print("\n[Step 6] Verifying owner information...")
    
    assert 'owner_email' in shared_diagram, "Owner email not in response"
    assert shared_diagram['owner_email'] == user_a_email, f"Owner email mismatch: expected {user_a_email}, got {shared_diagram['owner_email']}"
    print(f"✓ Owner shown correctly: {shared_diagram['owner_email']}")
    
    # Step 7: Verify permission level shown
    print("\n[Step 7] Verifying permission level...")
    
    assert 'permission' in shared_diagram, "Permission not in response"
    assert shared_diagram['permission'] == 'view', f"Permission mismatch: expected 'view', got {shared_diagram['permission']}"
    print(f"✓ Permission level shown correctly: {shared_diagram['permission']}")
    
    # Step 8: User A creates and shares another diagram (edit permission)
    print("\n[Step 8] User A creates and shares another diagram (edit permission)...")
    
    response = requests.post(f"{BASE_URL_DIAGRAM}/", 
        headers={"X-User-ID": user_a_id},
        json={
            "title": "Second Shared Diagram",
            "file_type": "note",
            "note_content": "This is a note"
        }
    )
    assert response.status_code in [200, 201], f"Diagram 2 creation failed: {response.status_code} - {response.text}"
    diagram_2 = response.json()
    diagram_2_id = diagram_2['id']
    print(f"✓ Second diagram created (ID: {diagram_2_id})")
    
    response = requests.post(f"{BASE_URL_DIAGRAM}/{diagram_2_id}/share",
        headers={"X-User-ID": user_a_id},
        json={
            "shared_with_email": user_b_email,
            "permission": "edit"
        }
    )
    assert response.status_code == 200, f"Share 2 creation failed: {response.text}"
    share_2 = response.json()
    print(f"✓ Second diagram shared with User B (edit permission)")
    
    # Step 9: Verify new diagram appears in list
    print("\n[Step 9] Verifying new diagram appears in shared list...")
    
    response = requests.get(f"{BASE_URL_DIAGRAM}/shared-with-me",
        headers={"X-User-ID": user_b_id}
    )
    assert response.status_code == 200, f"Shared with me request failed: {response.text}"
    shared_data = response.json()
    
    assert shared_data['total'] == 2, f"Expected 2 shared diagrams, got {shared_data['total']}"
    print(f"✓ Now showing {shared_data['total']} shared diagrams")
    
    # Verify both diagrams are in the list
    diagram_ids = [d['id'] for d in shared_data['diagrams']]
    assert diagram_1_id in diagram_ids, "First diagram not in list"
    assert diagram_2_id in diagram_ids, "Second diagram not in list"
    print(f"✓ Both diagrams present in list")
    
    # Verify permissions are correct
    for diagram in shared_data['diagrams']:
        if diagram['id'] == diagram_1_id:
            assert diagram['permission'] == 'view', "Diagram 1 permission incorrect"
            print(f"  - Diagram 1: {diagram['title']} (permission: {diagram['permission']})")
        elif diagram['id'] == diagram_2_id:
            assert diagram['permission'] == 'edit', "Diagram 2 permission incorrect"
            print(f"  - Diagram 2: {diagram['title']} (permission: {diagram['permission']})")
    
    # Step 10: Verify User B cannot see User A's other diagrams
    print("\n[Step 10] Verifying User B only sees shared diagrams...")
    
    # User A creates a diagram but doesn't share it
    response = requests.post(f"{BASE_URL_DIAGRAM}/", 
        headers={"X-User-ID": user_a_id},
        json={
            "title": "Private Diagram",
            "file_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )
    assert response.status_code in [200, 201], f"Private diagram creation failed: {response.status_code} - {response.text}"
    private_diagram = response.json()
    print(f"✓ User A created private diagram (not shared)")
    
    # User B checks shared list again
    response = requests.get(f"{BASE_URL_DIAGRAM}/shared-with-me",
        headers={"X-User-ID": user_b_id}
    )
    assert response.status_code == 200, f"Shared with me request failed: {response.text}"
    shared_data = response.json()
    
    # Should still be 2 diagrams
    assert shared_data['total'] == 2, f"Expected 2 shared diagrams, got {shared_data['total']}"
    diagram_ids = [d['id'] for d in shared_data['diagrams']]
    assert private_diagram['id'] not in diagram_ids, "Private diagram should not appear in shared list"
    print(f"✓ Private diagram not visible to User B (correct)")
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nFeature #154 'Shared with me' is working correctly!")
    print("\nSummary:")
    print(f"  - User A: {user_a_email}")
    print(f"  - User B: {user_b_email}")
    print(f"  - Shared diagrams: 2")
    print(f"  - Diagram 1: {diagram_1['title']} (view permission)")
    print(f"  - Diagram 2: {diagram_2['title']} (edit permission)")
    print(f"  - Private diagram not visible: ✓")
    
    return True

if __name__ == "__main__":
    try:
        test_feature_154()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
