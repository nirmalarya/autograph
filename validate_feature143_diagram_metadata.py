#!/usr/bin/env python3
"""
Feature #143 Validation: Diagram metadata: creator, last edited by, view count

Tests:
1. User A creates diagram → verify creator=User A (owner_id) in database
2. User B (with edit permission) edits diagram → verify last_edited_by=User B
3. User C views diagram → verify view_count incremented
4. View diagram 10 times → verify view_count=10
5. Check metadata panel → verify all metadata displayed correctly
"""

import requests
import time
import psycopg2

BASE_URL = "http://localhost:8080"  # API Gateway
AUTH_SERVICE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"

def verify_email_in_db(user_id):
    """Mark user as verified in database."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def register_and_login_user(email, password, full_name):
    """Register a user, verify email, and login."""
    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )

    if register_response.status_code != 201:
        raise Exception(f"Registration failed: {register_response.text}")

    user_data = register_response.json()
    user_id = user_data["id"]

    # Verify email in database
    verify_email_in_db(user_id)

    # Login to get token
    login_response = requests.post(
        f"{AUTH_SERVICE}/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        raise Exception(f"Login failed: {login_response.text}")

    token_data = login_response.json()

    return {
        "id": user_id,
        "email": email,
        "access_token": token_data["access_token"]
    }

def test_feature_143():
    """Test diagram metadata tracking."""
    print("=" * 80)
    print("FEATURE #143: Diagram Metadata (creator, last_edited_by, view_count)")
    print("=" * 80)

    # Step 1: Register User A (Creator)
    print("\n1. Registering User A (creator)...")
    user_a_email = f"creator_{int(time.time())}@test.com"
    user_a_password = "Password123!@#"

    user_a = register_and_login_user(user_a_email, user_a_password, "User A Creator")
    user_a_id = user_a['id']
    user_a_token = user_a['access_token']
    print(f"   ✓ User A registered (ID: {user_a_id})")

    # Step 2: User A creates a diagram
    print("\n2. User A creates a diagram...")
    create_response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {user_a_token}",
            "X-User-ID": user_a_id
        },
        json={
            "title": "Feature 143 Test Diagram",
            "file_type": "canvas",
            "canvas_data": {"shapes": [{"id": "1", "type": "rectangle"}]}
        }
    )
    print(f"   Status: {create_response.status_code}")
    assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
    diagram = create_response.json()
    diagram_id = diagram['id']
    print(f"   ✓ Diagram created (ID: {diagram_id})")

    # Step 3: Verify creator metadata
    print("\n3. Verifying creator (owner_id) = User A...")
    assert diagram['owner_id'] == user_a_id, f"Expected owner_id={user_a_id}, got {diagram['owner_id']}"
    print(f"   ✓ Creator (owner_id): {diagram['owner_id']}")
    print(f"   ✓ View count: {diagram['view_count']}")
    print(f"   ✓ Last edited by: {diagram.get('last_edited_by')}")
    initial_view_count = diagram['view_count']

    # Step 4: Register User B (Editor)
    print("\n4. Registering User B (editor)...")
    user_b_email = f"editor_{int(time.time())}@test.com"
    user_b_password = "Password123!@#"

    user_b = register_and_login_user(user_b_email, user_b_password, "User B Editor")
    user_b_id = user_b['id']
    user_b_token = user_b['access_token']
    print(f"   ✓ User B registered (ID: {user_b_id})")

    # Step 5: User A shares diagram with User B (edit permission)
    print("\n5. User A shares diagram with User B (edit permission)...")
    share_response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/share",
        headers={
            "Authorization": f"Bearer {user_a_token}",
            "X-User-ID": user_a_id
        },
        json={
            "permission": "edit",
            "is_public": False,
            "shared_with_email": user_b_email
        }
    )
    print(f"   Status: {share_response.status_code}")
    assert share_response.status_code in [200, 201], f"Share failed: {share_response.text}"
    print(f"   ✓ Diagram shared with User B (edit permission)")

    # Step 6: User B edits the diagram
    print("\n6. User B edits the diagram...")
    update_response = requests.put(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user_b_token}",
            "X-User-ID": user_b_id
        },
        json={
            "title": "Feature 143 Test Diagram - Edited by User B",
            "canvas_data": {"shapes": [{"id": "1", "type": "rectangle"}, {"id": "2", "type": "circle"}]}
        }
    )
    print(f"   Status: {update_response.status_code}")
    assert update_response.status_code == 200, f"Update failed: {update_response.text}"
    updated_diagram = update_response.json()
    print(f"   ✓ Diagram updated by User B")

    # Step 7: Verify last_edited_by = User B
    print("\n7. Verifying last_edited_by = User B...")
    assert updated_diagram['last_edited_by'] == user_b_id, f"Expected last_edited_by={user_b_id}, got {updated_diagram.get('last_edited_by')}"
    print(f"   ✓ Last edited by: {updated_diagram['last_edited_by']} (User B)")
    print(f"   ✓ Creator still: {updated_diagram['owner_id']} (User A)")

    # Step 8: Register User C (Viewer)
    print("\n8. Registering User C (viewer)...")
    user_c_email = f"viewer_{int(time.time())}@test.com"
    user_c_password = "Password123!@#"

    user_c = register_and_login_user(user_c_email, user_c_password, "User C Viewer")
    user_c_id = user_c['id']
    user_c_token = user_c['access_token']
    print(f"   ✓ User C registered (ID: {user_c_id})")

    # Step 9: User A shares diagram with User C (view permission)
    print("\n9. User A shares diagram with User C (view permission)...")
    share_response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/share",
        headers={
            "Authorization": f"Bearer {user_a_token}",
            "X-User-ID": user_a_id
        },
        json={
            "permission": "view",
            "is_public": False,
            "shared_with_email": user_c_email
        }
    )
    print(f"   Status: {share_response.status_code}")
    assert share_response.status_code in [200, 201]
    print(f"   ✓ Diagram shared with User C (view permission)")

    # Step 10: User C views the diagram (should increment view_count)
    print("\n10. User C views the diagram...")
    view_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user_c_token}",
            "X-User-ID": user_c_id
        }
    )
    print(f"   Status: {view_response.status_code}")
    assert view_response.status_code == 200, f"View failed: {view_response.text}"
    viewed_diagram = view_response.json()
    print(f"   ✓ Diagram viewed by User C")
    print(f"   ✓ View count: {viewed_diagram['view_count']}")

    # Step 11: Verify view_count incremented
    print("\n11. Verifying view_count incremented...")
    current_view_count = viewed_diagram['view_count']
    assert current_view_count > initial_view_count, f"View count should increase: {initial_view_count} → {current_view_count}"
    print(f"   ✓ View count increased: {initial_view_count} → {current_view_count}")

    # Step 12: View diagram 10 more times (User A)
    print("\n12. User A views diagram 10 more times...")
    for i in range(10):
        view_response = requests.get(
            f"{DIAGRAM_SERVICE}/{diagram_id}",
            headers={
                "Authorization": f"Bearer {user_a_token}",
                "X-User-ID": user_a_id
            }
        )
        assert view_response.status_code == 200
        print(f"   View {i+1}/10: view_count = {view_response.json()['view_count']}")

    final_diagram = view_response.json()
    final_view_count = final_diagram['view_count']
    print(f"   ✓ Final view count: {final_view_count}")

    # Step 13: Verify all metadata fields are present
    print("\n13. Verifying all metadata fields present...")
    assert 'owner_id' in final_diagram, "Missing owner_id (creator)"
    assert 'last_edited_by' in final_diagram, "Missing last_edited_by"
    assert 'view_count' in final_diagram, "Missing view_count"
    assert 'created_at' in final_diagram, "Missing created_at"
    assert 'updated_at' in final_diagram, "Missing updated_at"
    assert 'last_accessed_at' in final_diagram, "Missing last_accessed_at"
    assert 'last_activity' in final_diagram, "Missing last_activity"
    print("   ✓ owner_id (creator):", final_diagram['owner_id'])
    print("   ✓ last_edited_by:", final_diagram['last_edited_by'])
    print("   ✓ view_count:", final_diagram['view_count'])
    print("   ✓ created_at:", final_diagram['created_at'])
    print("   ✓ updated_at:", final_diagram['updated_at'])
    print("   ✓ last_accessed_at:", final_diagram.get('last_accessed_at'))
    print("   ✓ last_activity:", final_diagram.get('last_activity'))

    # Step 14: Verify metadata correctness
    print("\n14. Verifying metadata correctness...")
    assert final_diagram['owner_id'] == user_a_id, "Creator should be User A"
    assert final_diagram['last_edited_by'] == user_b_id, "Last editor should be User B"
    assert final_diagram['view_count'] >= 10, f"View count should be ≥10, got {final_diagram['view_count']}"
    print("   ✓ Creator (owner_id) = User A:", user_a_id)
    print("   ✓ Last edited by = User B:", user_b_id)
    print("   ✓ View count ≥ 10:", final_diagram['view_count'])

    print("\n" + "=" * 80)
    print("✅ FEATURE #143 VALIDATION PASSED")
    print("=" * 80)
    print("\nSUMMARY:")
    print(f"  • Creator (owner_id): {final_diagram['owner_id']}")
    print(f"  • Last edited by: {final_diagram['last_edited_by']}")
    print(f"  • View count: {final_diagram['view_count']}")
    print(f"  • Created at: {final_diagram['created_at']}")
    print(f"  • Updated at: {final_diagram['updated_at']}")
    print(f"  • Last accessed: {final_diagram.get('last_accessed_at')}")
    print(f"  • Last activity: {final_diagram.get('last_activity')}")
    print("\nAll diagram metadata is properly tracked and returned!")
    return True

if __name__ == "__main__":
    try:
        test_feature_143()
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
