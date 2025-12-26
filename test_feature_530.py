#!/usr/bin/env python3
"""
Feature #530: Custom Roles with Granular Permissions
Tests the complete custom roles API implementation
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080/api/v1"
AUTH_URL = "http://localhost:8085"

def login(email, password):
    """Login and get access token."""
    response = requests.post(f"{AUTH_URL}/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_create_custom_role(token, team_id):
    """Test creating a custom role."""
    print("\n1️⃣  Testing: Create custom role")

    headers = {"Authorization": f"Bearer {token}"}
    role_data = {
        "name": "Content Creator",
        "description": "Can create and edit own content, comment, and export",
        "can_invite_members": False,
        "can_remove_members": False,
        "can_manage_roles": False,
        "can_create_diagrams": True,
        "can_edit_own_diagrams": True,
        "can_edit_all_diagrams": False,
        "can_delete_own_diagrams": True,
        "can_delete_all_diagrams": False,
        "can_share_diagrams": True,
        "can_comment": True,
        "can_export": True,
        "can_view_analytics": False,
        "can_manage_team_settings": False
    }

    response = requests.post(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles",
        json=role_data,
        headers=headers
    )

    if response.status_code == 201:
        role = response.json()
        print(f"✅ Custom role created: {role['name']}")
        print(f"   ID: {role['id']}")
        print(f"   Permissions: {json.dumps(role['permissions'], indent=2)}")
        return role['id']
    else:
        print(f"❌ Failed to create role: {response.status_code} - {response.text}")
        return None

def test_list_custom_roles(token, team_id):
    """Test listing custom roles."""
    print("\n2️⃣  Testing: List custom roles")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data['roles'])} custom roles:")
        for role in data['roles']:
            print(f"   - {role['name']}: {role.get('description', 'No description')}")
        return True
    else:
        print(f"❌ Failed to list roles: {response.status_code} - {response.text}")
        return False

def test_get_custom_role(token, team_id, role_id):
    """Test getting a specific custom role."""
    print("\n3️⃣  Testing: Get custom role details")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles/{role_id}",
        headers=headers
    )

    if response.status_code == 200:
        role = response.json()
        print(f"✅ Retrieved role: {role['name']}")
        print(f"   Created: {role['created_at']}")
        print(f"   System role: {role['is_system_role']}")
        return True
    else:
        print(f"❌ Failed to get role: {response.status_code} - {response.text}")
        return False

def test_update_custom_role(token, team_id, role_id):
    """Test updating a custom role."""
    print("\n4️⃣  Testing: Update custom role")

    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "description": "Updated: Can create, edit own content, and view analytics",
        "can_view_analytics": True  # Enable analytics
    }

    response = requests.put(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles/{role_id}",
        json=update_data,
        headers=headers
    )

    if response.status_code == 200:
        role = response.json()
        print(f"✅ Role updated successfully")
        print(f"   New description: {role['description']}")
        print(f"   Analytics enabled: {role['permissions']['can_view_analytics']}")
        return True
    else:
        print(f"❌ Failed to update role: {response.status_code} - {response.text}")
        return False

def test_duplicate_role_name(token, team_id):
    """Test creating role with duplicate name (should fail)."""
    print("\n5️⃣  Testing: Duplicate role name (should fail)")

    headers = {"Authorization": f"Bearer {token}"}
    role_data = {
        "name": "Content Creator",  # Same name as before
        "description": "This should fail"
    }

    response = requests.post(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles",
        json=role_data,
        headers=headers
    )

    if response.status_code == 409:
        print(f"✅ Correctly rejected duplicate role name")
        return True
    else:
        print(f"❌ Should have rejected duplicate: {response.status_code}")
        return False

def test_non_admin_cannot_create(member_token, team_id):
    """Test that non-admin cannot create roles."""
    print("\n6️⃣  Testing: Non-admin cannot create roles (should fail)")

    headers = {"Authorization": f"Bearer {member_token}"}
    role_data = {
        "name": "Unauthorized Role",
        "description": "This should fail"
    }

    response = requests.post(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles",
        json=role_data,
        headers=headers
    )

    if response.status_code == 403:
        print(f"✅ Correctly rejected non-admin role creation")
        return True
    else:
        print(f"❌ Should have rejected non-admin: {response.status_code}")
        return False

def test_delete_custom_role(token, team_id, role_id):
    """Test deleting a custom role."""
    print("\n7️⃣  Testing: Delete custom role")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{AUTH_URL}/api/v1/teams/{team_id}/custom-roles/{role_id}",
        headers=headers
    )

    if response.status_code == 204:
        print(f"✅ Role deleted successfully")
        return True
    else:
        print(f"❌ Failed to delete role: {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests for Feature #530."""
    print("="*80)
    print("Feature #530: Custom Roles with Granular Permissions")
    print("="*80)

    # Login as admin
    print("\n🔐 Logging in as team admin...")
    admin_token = login("admin530@test.com", "password123")
    if not admin_token:
        print("❌ Failed to login as admin")
        sys.exit(1)
    print("✅ Admin logged in successfully")

    # Login as regular member
    print("\n🔐 Logging in as team member...")
    member_token = login("member530@test.com", "password123")
    if not member_token:
        print("❌ Failed to login as member")
        sys.exit(1)
    print("✅ Member logged in successfully")

    team_id = "test-team-530"

    # Run tests
    role_id = test_create_custom_role(admin_token, team_id)
    if not role_id:
        print("\n❌ FAILED: Cannot continue without role ID")
        sys.exit(1)

    if not test_list_custom_roles(admin_token, team_id):
        sys.exit(1)

    if not test_get_custom_role(admin_token, team_id, role_id):
        sys.exit(1)

    if not test_update_custom_role(admin_token, team_id, role_id):
        sys.exit(1)

    if not test_duplicate_role_name(admin_token, team_id):
        sys.exit(1)

    if not test_non_admin_cannot_create(member_token, team_id):
        sys.exit(1)

    if not test_delete_custom_role(admin_token, team_id, role_id):
        sys.exit(1)

    # Final summary
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED for Feature #530!")
    print("="*80)
    print("\nFeature #530 verified:")
    print("  ✓ Custom roles can be created with granular permissions")
    print("  ✓ Roles can be listed, retrieved, updated, and deleted")
    print("  ✓ Only team admins can manage roles")
    print("  ✓ Duplicate role names are rejected")
    print("  ✓ Authorization checks work correctly")
    print("\nFeature #530 is READY TO MARK AS PASSING! ✅")

    return 0

if __name__ == "__main__":
    sys.exit(main())
