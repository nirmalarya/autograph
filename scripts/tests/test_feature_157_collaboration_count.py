"""
Test Feature #157: Diagram collaboration count tracking

This test verifies:
1. User A creates diagram - collaborator_count=1 (owner)
2. Share with User B - collaborator_count=2
3. Share with User C and D - collaborator_count=4
4. Remove User B's access - collaborator_count=3
"""

import requests
import json
import time

# Configuration
API_BASE = "http://localhost:8080/api"
AUTH_BASE = f"{API_BASE}/auth"
DIAGRAM_BASE = f"{API_BASE}/diagrams"

def register_user(email, password, full_name):
    """Register a new user."""
    response = requests.post(
        f"{AUTH_BASE}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )
    return response

def login_user(email, password):
    """Login and get access token."""
    response = requests.post(
        f"{AUTH_BASE}/login",
        json={
            "email": email,
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_diagram(token, title, file_type="canvas"):
    """Create a new diagram."""
    response = requests.post(
        f"{DIAGRAM_BASE}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "file_type": file_type,
            "canvas_data": {"shapes": []},
            "note_content": "Test diagram for collaboration count"
        }
    )
    return response

def get_diagram(token, diagram_id):
    """Get diagram details."""
    response = requests.get(
        f"{DIAGRAM_BASE}/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def create_share(token, diagram_id, shared_with_email, permission="view"):
    """Share diagram with a specific user."""
    response = requests.post(
        f"{DIAGRAM_BASE}/{diagram_id}/share",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "shared_with_email": shared_with_email,
            "permission": permission
        }
    )
    return response

def revoke_share(token, diagram_id, share_id):
    """Revoke a share link."""
    response = requests.delete(
        f"{DIAGRAM_BASE}/{diagram_id}/share/{share_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def main():
    print("Testing Feature #157: Diagram collaboration count tracking")
    print("=" * 80)
    
    # Generate unique test data
    timestamp = int(time.time())
    user_a_email = f"collab_test_a_{timestamp}@example.com"
    user_b_email = f"collab_test_b_{timestamp}@example.com"
    user_c_email = f"collab_test_c_{timestamp}@example.com"
    user_d_email = f"collab_test_d_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Test 1: Register User A
    print("\n[Test 1] Registering User A...")
    response = register_user(user_a_email, password, "User A")
    if response.status_code == 201:
        user_a_id = response.json()["id"]
        print(f"✅ User A registered: {user_a_email} (ID: {user_a_id})")
    else:
        print(f"❌ Failed to register User A: {response.status_code} - {response.text}")
        return
    
    # Test 2: Register User B
    print("\n[Test 2] Registering User B...")
    response = register_user(user_b_email, password, "User B")
    if response.status_code == 201:
        user_b_id = response.json()["id"]
        print(f"✅ User B registered: {user_b_email} (ID: {user_b_id})")
    else:
        print(f"❌ Failed to register User B: {response.status_code} - {response.text}")
        return
    
    # Test 3: Register User C
    print("\n[Test 3] Registering User C...")
    response = register_user(user_c_email, password, "User C")
    if response.status_code == 201:
        user_c_id = response.json()["id"]
        print(f"✅ User C registered: {user_c_email} (ID: {user_c_id})")
    else:
        print(f"❌ Failed to register User C: {response.status_code} - {response.text}")
        return
    
    # Test 4: Register User D
    print("\n[Test 4] Registering User D...")
    response = register_user(user_d_email, password, "User D")
    if response.status_code == 201:
        user_d_id = response.json()["id"]
        print(f"✅ User D registered: {user_d_email} (ID: {user_d_id})")
    else:
        print(f"❌ Failed to register User D: {response.status_code} - {response.text}")
        return
    
    # Test 5: Login User A
    print("\n[Test 5] Logging in User A...")
    token_a = login_user(user_a_email, password)
    if token_a:
        print(f"✅ User A logged in successfully")
    else:
        print(f"❌ Failed to login User A")
        return
    
    # Test 6: User A creates diagram
    print("\n[Test 6] User A creating diagram...")
    response = create_diagram(token_a, "Collaboration Test Diagram")
    if response.status_code in [200, 201]:
        diagram_id = response.json()["id"]
        print(f"✅ Diagram created: {diagram_id}")
    else:
        print(f"❌ Failed to create diagram: {response.status_code} - {response.text}")
        return
    
    # Test 7: Verify initial collaborator_count=1 (owner only)
    print("\n[Test 7] Verifying initial collaborator_count=1...")
    response = get_diagram(token_a, diagram_id)
    if response.status_code == 200:
        diagram = response.json()
        collaborator_count = diagram.get("collaborator_count", 0)
        if collaborator_count == 1:
            print(f"✅ Initial collaborator count is correct: {collaborator_count}")
        else:
            print(f"❌ Expected collaborator_count=1, got {collaborator_count}")
            return
    else:
        print(f"❌ Failed to get diagram: {response.status_code} - {response.text}")
        return
    
    # Test 8: Share with User B
    print("\n[Test 8] Sharing diagram with User B...")
    response = create_share(token_a, diagram_id, user_b_email)
    if response.status_code == 200:
        share_b_id = response.json()["share_id"]
        print(f"✅ Shared with User B (Share ID: {share_b_id})")
    else:
        print(f"❌ Failed to share with User B: {response.status_code} - {response.text}")
        return
    
    # Test 9: Verify collaborator_count=2
    print("\n[Test 9] Verifying collaborator_count=2...")
    response = get_diagram(token_a, diagram_id)
    if response.status_code == 200:
        diagram = response.json()
        collaborator_count = diagram.get("collaborator_count", 0)
        if collaborator_count == 2:
            print(f"✅ Collaborator count is correct: {collaborator_count}")
        else:
            print(f"❌ Expected collaborator_count=2, got {collaborator_count}")
            return
    else:
        print(f"❌ Failed to get diagram: {response.status_code} - {response.text}")
        return
    
    # Test 10: Share with User C
    print("\n[Test 10] Sharing diagram with User C...")
    response = create_share(token_a, diagram_id, user_c_email)
    if response.status_code == 200:
        share_c_id = response.json()["share_id"]
        print(f"✅ Shared with User C (Share ID: {share_c_id})")
    else:
        print(f"❌ Failed to share with User C: {response.status_code} - {response.text}")
        return
    
    # Test 11: Share with User D
    print("\n[Test 11] Sharing diagram with User D...")
    response = create_share(token_a, diagram_id, user_d_email)
    if response.status_code == 200:
        share_d_id = response.json()["share_id"]
        print(f"✅ Shared with User D (Share ID: {share_d_id})")
    else:
        print(f"❌ Failed to share with User D: {response.status_code} - {response.text}")
        return
    
    # Test 12: Verify collaborator_count=4
    print("\n[Test 12] Verifying collaborator_count=4...")
    response = get_diagram(token_a, diagram_id)
    if response.status_code == 200:
        diagram = response.json()
        collaborator_count = diagram.get("collaborator_count", 0)
        if collaborator_count == 4:
            print(f"✅ Collaborator count is correct: {collaborator_count}")
        else:
            print(f"❌ Expected collaborator_count=4, got {collaborator_count}")
            return
    else:
        print(f"❌ Failed to get diagram: {response.status_code} - {response.text}")
        return
    
    # Test 13: Revoke User B's access
    print("\n[Test 13] Revoking User B's access...")
    response = revoke_share(token_a, diagram_id, share_b_id)
    if response.status_code == 200:
        print(f"✅ User B's access revoked")
    else:
        print(f"❌ Failed to revoke User B's access: {response.status_code} - {response.text}")
        return
    
    # Test 14: Verify collaborator_count=3
    print("\n[Test 14] Verifying collaborator_count=3...")
    response = get_diagram(token_a, diagram_id)
    if response.status_code == 200:
        diagram = response.json()
        collaborator_count = diagram.get("collaborator_count", 0)
        if collaborator_count == 3:
            print(f"✅ Collaborator count is correct: {collaborator_count}")
        else:
            print(f"❌ Expected collaborator_count=3, got {collaborator_count}")
            return
    else:
        print(f"❌ Failed to get diagram: {response.status_code} - {response.text}")
        return
    
    # Test 15: Verify collaborator_count field exists in metadata
    print("\n[Test 15] Verifying collaborator_count field in metadata...")
    if "collaborator_count" in diagram:
        print(f"✅ collaborator_count field exists: {diagram['collaborator_count']}")
    else:
        print(f"❌ collaborator_count field missing from response")
        return
    
    print("\n" + "=" * 80)
    print("✅ All tests passed! Feature #157 is working correctly.")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
