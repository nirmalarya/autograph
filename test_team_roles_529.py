#!/usr/bin/env python3
"""Test Feature #529: Enterprise: Team management: assign roles

Tests role assignment and update functionality:
1. Select user
2. Change role to 'Admin' (or other role)
3. Save
4. Verify role updated
5. Verify permissions changed
"""
import requests
import json
import time
import subprocess

# Configuration
BASE_URL = "http://localhost:8080/api"  # Via API Gateway

def create_test_user(username_prefix="user"):
    """Create a test user for team testing."""
    timestamp = int(time.time())
    username = f"{username_prefix}_{timestamp}"
    email = f"{username}@test.com"
    password = "TestPass123!"

    # Register user
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Test User {timestamp}"
        }
    )

    if response.status_code not in [200, 201]:
        return None, None, None

    # Get user ID
    reg_data = response.json()
    user_id = reg_data.get("user_id") or reg_data.get("id")

    # Verify email via SQL
    verify_sql = f"UPDATE users SET is_verified = TRUE WHERE email = '{email}';"
    subprocess.run(
        ["docker", "exec", "-i", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", verify_sql],
        capture_output=True
    )

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code != 200:
        return None, None, None

    access_token = response.json().get("access_token")
    return email, access_token, user_id


def create_team(admin_token):
    """Create a test team."""
    timestamp = int(time.time())
    team_name = f"Test Team {timestamp}"

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams",
        headers=headers,
        json={"name": team_name, "plan": "enterprise", "max_members": 10}
    )

    return response.json() if response.status_code in [200, 201] else None


def invite_member(team_id, admin_token, member_email, role="editor"):
    """Invite a member to the team."""
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json={"email": member_email, "role": role}
    )

    return response.json() if response.status_code in [200, 201] else None


def get_user_id_by_email(email):
    """Get user ID from database by email."""
    result = subprocess.run(
        ["docker", "exec", "-i", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
         "-t", "-c", f"SELECT id FROM users WHERE email = '{email}';"],
        capture_output=True,
        text=True
    )
    user_id = result.stdout.strip()
    return user_id if user_id else None


def update_member_role(team_id, user_id, new_role, admin_token):
    """
    Steps 1-3: Select user, Change role, Save
    """
    print(f"\n👤 Updating role for user {user_id} to: {new_role}")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    response = requests.put(
        f"{BASE_URL}/auth/teams/{team_id}/members/{user_id}/role",
        headers=headers,
        json={"role": new_role}
    )

    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ❌ Role update failed")
        print(f"   Response: {response.text}")
        return None

    member = response.json()
    print(f"   ✅ Role updated successfully!")
    print(f"   New Role: {member['role']}")

    return member


def verify_role(team_id, user_id, expected_role, admin_token):
    """
    Step 4: Verify role updated
    """
    print(f"\n✅ Verifying role for user {user_id}...")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{BASE_URL}/auth/teams/{team_id}/members",
        headers=headers
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to get team members")
        return False

    members = response.json().get("members", [])

    for member in members:
        if member['user_id'] == user_id:
            actual_role = member['role']
            if actual_role == expected_role:
                print(f"   ✅ Role verified: {actual_role}")
                return True
            else:
                print(f"   ❌ Role mismatch! Expected: {expected_role}, Got: {actual_role}")
                return False

    print(f"   ❌ User not found in team")
    return False


def test_permissions_after_role_change(team_id, member_token, member_email, test_name):
    """
    Step 5: Verify permissions changed
    Test if member can now invite others (admin permission)
    """
    print(f"\n🔐 Testing permissions for: {test_name}")

    headers = {
        "Authorization": f"Bearer {member_token}",
        "Content-Type": "application/json"
    }

    # Try to invite someone (only admins can do this)
    test_invite_email = f"test_{int(time.time())}@test.com"

    # First create the user to invite
    test_email, test_token, test_id = create_test_user("perm_test")
    if not test_email:
        print(f"   ⚠️  Could not create test user for permission check")
        return None

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json={"email": test_email, "role": "viewer"}
    )

    status_code = response.status_code

    if status_code == 201:
        print(f"   ✅ Permission granted - can invite members (admin/owner)")
        return True
    elif status_code == 403:
        print(f"   ✅ Permission denied - cannot invite members (non-admin)")
        return False
    else:
        print(f"   ⚠️  Unexpected status: {status_code}")
        print(f"   Response: {response.text}")
        return None


def run_feature_529_test():
    """Run complete test for Feature #529."""
    print("\n" + "="*70)
    print("FEATURE #529: Enterprise Team Management - Assign Roles")
    print("="*70)

    test_results = []

    try:
        # Setup: Create admin user
        print("\n[Setup] Creating admin user...")
        admin_email, admin_token, admin_id = create_test_user("admin")
        if not admin_token:
            print("\n❌ Failed to create admin user")
            return False

        # Setup: Create team
        print("\n[Setup] Creating team...")
        team = create_team(admin_token)
        if not team:
            print("\n❌ Failed to create team")
            return False

        team_id = team['id']
        print(f"   Team ID: {team_id}")

        # Setup: Create and invite members
        print("\n[Setup] Creating test members...")
        member1_email, member1_token, member1_id = create_test_user("member1")
        member2_email, member2_token, member2_id = create_test_user("member2")

        if not member1_email or not member2_email:
            print("\n❌ Failed to create test members")
            return False

        # Invite members with initial roles
        print(f"\n[Setup] Inviting member1 as 'editor'...")
        member1 = invite_member(team_id, admin_token, member1_email, "editor")
        test_results.append(("Setup: Invite member1", member1 is not None))

        print(f"\n[Setup] Inviting member2 as 'viewer'...")
        member2 = invite_member(team_id, admin_token, member2_email, "viewer")
        test_results.append(("Setup: Invite member2", member2 is not None))

        # Get actual user IDs from database
        actual_member1_id = get_user_id_by_email(member1_email)
        actual_member2_id = get_user_id_by_email(member2_email)

        if not actual_member1_id or not actual_member2_id:
            print("\n❌ Failed to get user IDs")
            return False

        print(f"   Member1 ID: {actual_member1_id}")
        print(f"   Member2 ID: {actual_member2_id}")

        # Test 1: Change editor to admin
        print("\n" + "-"*70)
        print("[Test 1] Change member1 role from 'editor' to 'admin'")
        print("-"*70)

        # Step 5: Check current permissions (editor - cannot invite)
        can_invite_before = test_permissions_after_role_change(
            team_id, member1_token, member1_email, "member1 as editor (before)"
        )
        test_results.append(("Editor cannot invite (before)", can_invite_before == False))

        # Steps 1-3: Update role
        updated_member1 = update_member_role(team_id, actual_member1_id, "admin", admin_token)
        test_results.append(("Update member1 to admin", updated_member1 is not None))

        # Step 4: Verify role updated
        if updated_member1:
            verified1 = verify_role(team_id, actual_member1_id, "admin", admin_token)
            test_results.append(("Verify member1 is admin", verified1))

            # Step 5: Verify permissions changed (admin - can invite)
            can_invite_after = test_permissions_after_role_change(
                team_id, member1_token, member1_email, "member1 as admin (after)"
            )
            test_results.append(("Admin can invite (after)", can_invite_after == True))

        # Test 2: Change viewer to editor
        print("\n" + "-"*70)
        print("[Test 2] Change member2 role from 'viewer' to 'editor'")
        print("-"*70)

        updated_member2 = update_member_role(team_id, actual_member2_id, "editor", admin_token)
        test_results.append(("Update member2 to editor", updated_member2 is not None))

        if updated_member2:
            verified2 = verify_role(team_id, actual_member2_id, "editor", admin_token)
            test_results.append(("Verify member2 is editor", verified2))

        # Test 3: Try invalid role
        print("\n" + "-"*70)
        print("[Test 3] Try to assign invalid role (should fail)")
        print("-"*70)

        print(f"\n👤 Attempting to set invalid role 'superadmin'...")
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        response = requests.put(
            f"{BASE_URL}/auth/teams/{team_id}/members/{actual_member2_id}/role",
            headers=headers,
            json={"role": "superadmin"}
        )

        if response.status_code == 400:
            print(f"   ✅ Correctly rejected invalid role (400)")
            test_results.append(("Reject invalid role", True))
        else:
            print(f"   ⚠️  Expected 400, got {response.status_code}")
            test_results.append(("Reject invalid role", False))

        # Test 4: Non-admin trying to change roles
        print("\n" + "-"*70)
        print("[Test 4] Non-admin trying to change roles (should fail)")
        print("-"*70)

        print(f"\n🚫 Member2 (editor) trying to change member1's role...")
        headers_member2 = {
            "Authorization": f"Bearer {member2_token}",
            "Content-Type": "application/json"
        }

        response = requests.put(
            f"{BASE_URL}/auth/teams/{team_id}/members/{actual_member1_id}/role",
            headers=headers_member2,
            json={"role": "viewer"}
        )

        if response.status_code == 403:
            print(f"   ✅ Correctly rejected non-admin role change (403)")
            test_results.append(("Reject non-admin role change", True))
        else:
            print(f"   ⚠️  Expected 403, got {response.status_code}")
            test_results.append(("Reject non-admin role change", False))

        # Summary
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)

        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)

        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")

        print(f"\n{passed}/{total} tests passed")

        if passed == total:
            print("\n" + "="*70)
            print("✅ FEATURE #529 TEST PASSED!")
            print("="*70)
            print("\nFeature Validation:")
            print("  ✅ Step 1-3: Select user, change role, save")
            print("  ✅ Step 4: Verify role updated correctly")
            print("  ✅ Step 5: Verify permissions changed (admin can invite)")
            print("  ✅ Invalid role rejected")
            print("  ✅ Non-admin role changes rejected")
            return True
        else:
            print(f"\n❌ {total - passed} test(s) failed")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_feature_529_test()
    exit(0 if success else 1)
