#!/usr/bin/env python3
"""Test Feature #528: Enterprise: Team management: invite members

Tests the complete invitation workflow:
1. Click 'Invite Member' (POST /teams/{team_id}/invite)
2. Enter email
3. Select role
4. Send invite
5. Verify email sent (for now auto-accepted)
6. User accepts (currently auto-accepted)
7. Verify added to team
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

    print(f"\n📝 Creating test user: {email}")

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
        print(f"   ❌ Registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None, None

    print(f"   ✅ User registered successfully")

    # Get user ID from registration response
    reg_data = response.json()
    user_id = reg_data.get("user_id") or reg_data.get("id")

    # Verify email directly via SQL (bypass email verification for testing)
    print(f"   📧 Verifying email via database...")
    verify_sql = f"UPDATE users SET is_verified = TRUE WHERE email = '{email}';"
    subprocess.run(
        ["docker", "exec", "-i", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", verify_sql],
        capture_output=True
    )

    # Login to get token
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code != 200:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None, None

    data = response.json()
    access_token = data.get("access_token")

    print(f"   ✅ Login successful, got access token")

    return email, access_token, user_id


def create_team(admin_token):
    """Create a test team."""
    timestamp = int(time.time())
    team_name = f"Test Team {timestamp}"

    print(f"\n🏢 Creating team: {team_name}")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    team_data = {
        "name": team_name,
        "plan": "enterprise",
        "max_members": 10
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams",
        headers=headers,
        json=team_data
    )

    if response.status_code not in [200, 201]:
        print(f"   ❌ Team creation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

    team = response.json()
    print(f"   ✅ Team created successfully!")
    print(f"   Team ID: {team['id']}")
    print(f"   Team Name: {team['name']}")

    return team


def test_invite_member(team_id, admin_token, member_email, role="editor"):
    """
    Step 1-4: Click 'Invite Member', Enter email, Select role, Send invite
    """
    print(f"\n👥 Inviting member: {member_email} with role: {role}")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    invite_data = {
        "email": member_email,
        "role": role
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json=invite_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code not in [200, 201]:
        print(f"   ❌ Member invitation failed")
        print(f"   Response: {response.text}")
        return None

    member = response.json()
    print(f"   ✅ Member invited successfully!")
    print(f"   Member ID: {member['id']}")
    print(f"   User Email: {member['user_email']}")
    print(f"   Role: {member['role']}")
    print(f"   Invitation Status: {member['invitation_status']}")

    return member


def verify_member_in_team(team_id, admin_token, expected_email):
    """
    Step 7: Verify user was added to team
    """
    print(f"\n✅ Verifying {expected_email} is in team...")

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
        print(f"   Response: {response.text}")
        return False

    data = response.json()
    members = data.get("members", [])

    for member in members:
        if member['user_email'] == expected_email:
            print(f"   ✅ Found {expected_email} in team!")
            print(f"      Role: {member['role']}")
            print(f"      Status: {member['invitation_status']}")
            return True

    print(f"   ❌ {expected_email} not found in team members")
    return False


def test_duplicate_invite(team_id, admin_token, member_email):
    """Test that inviting the same user twice fails gracefully."""
    print(f"\n🔄 Testing duplicate invitation for: {member_email}")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    invite_data = {
        "email": member_email,
        "role": "viewer"
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json=invite_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 409:  # Conflict
        print(f"   ✅ Correctly rejected duplicate invitation")
        return True
    else:
        print(f"   ⚠️  Expected 409 Conflict, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_invalid_email(team_id, admin_token):
    """Test inviting a non-existent user."""
    print(f"\n❌ Testing invitation with invalid email...")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    fake_email = f"nonexistent_{int(time.time())}@test.com"
    invite_data = {
        "email": fake_email,
        "role": "editor"
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json=invite_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 404:  # Not Found
        print(f"   ✅ Correctly rejected non-existent user")
        return True
    else:
        print(f"   ⚠️  Expected 404 Not Found, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_invalid_role(team_id, admin_token, member_email):
    """Test inviting with invalid role."""
    print(f"\n❌ Testing invitation with invalid role...")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    invite_data = {
        "email": member_email,
        "role": "superadmin"  # Invalid role
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json=invite_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 400:  # Bad Request
        print(f"   ✅ Correctly rejected invalid role")
        return True
    else:
        print(f"   ⚠️  Expected 400 Bad Request, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_non_admin_invite(team_id, member_token, another_email):
    """Test that non-admin members cannot invite others."""
    print(f"\n🚫 Testing non-admin trying to invite...")

    headers = {
        "Authorization": f"Bearer {member_token}",
        "Content-Type": "application/json"
    }

    invite_data = {
        "email": another_email,
        "role": "viewer"
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams/{team_id}/invite",
        headers=headers,
        json=invite_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code == 403:  # Forbidden
        print(f"   ✅ Correctly rejected non-admin invitation")
        return True
    else:
        print(f"   ⚠️  Expected 403 Forbidden, got {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def run_feature_528_test():
    """Run complete test for Feature #528."""
    print("\n" + "="*70)
    print("FEATURE #528: Enterprise Team Management - Invite Members")
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

        # Setup: Create users to invite
        print("\n[Setup] Creating users to invite...")
        member1_email, member1_token, member1_id = create_test_user("member1")
        member2_email, member2_token, member2_id = create_test_user("member2")
        member3_email, member3_token, member3_id = create_test_user("member3")

        if not member1_email or not member2_email:
            print("\n❌ Failed to create test users")
            return False

        # Test 1: Invite first member as editor
        print("\n" + "-"*70)
        print("[Test 1] Invite member with editor role")
        print("-"*70)
        result1 = test_invite_member(team_id, admin_token, member1_email, "editor")
        test_results.append(("Invite member 1 (editor)", result1 is not None))

        if result1:
            # Verify member was added
            verified1 = verify_member_in_team(team_id, admin_token, member1_email)
            test_results.append(("Verify member 1 in team", verified1))

        # Test 2: Invite second member as viewer
        print("\n" + "-"*70)
        print("[Test 2] Invite member with viewer role")
        print("-"*70)
        result2 = test_invite_member(team_id, admin_token, member2_email, "viewer")
        test_results.append(("Invite member 2 (viewer)", result2 is not None))

        if result2:
            verified2 = verify_member_in_team(team_id, admin_token, member2_email)
            test_results.append(("Verify member 2 in team", verified2))

        # Test 3: Try to invite duplicate member (should fail)
        print("\n" + "-"*70)
        print("[Test 3] Duplicate invitation (should fail)")
        print("-"*70)
        duplicate_test = test_duplicate_invite(team_id, admin_token, member1_email)
        test_results.append(("Reject duplicate invitation", duplicate_test))

        # Test 4: Invite with invalid email (should fail)
        print("\n" + "-"*70)
        print("[Test 4] Invalid email invitation (should fail)")
        print("-"*70)
        invalid_email_test = test_invalid_email(team_id, admin_token)
        test_results.append(("Reject invalid email", invalid_email_test))

        # Test 5: Invite with invalid role (should fail)
        if member3_email:
            print("\n" + "-"*70)
            print("[Test 5] Invalid role (should fail)")
            print("-"*70)
            invalid_role_test = test_invalid_role(team_id, admin_token, member3_email)
            test_results.append(("Reject invalid role", invalid_role_test))

        # Test 6: Non-admin trying to invite (should fail)
        if member1_token and member3_email:
            print("\n" + "-"*70)
            print("[Test 6] Non-admin invitation (should fail)")
            print("-"*70)
            non_admin_test = test_non_admin_invite(team_id, member1_token, member3_email)
            test_results.append(("Reject non-admin invitation", non_admin_test))

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
            print("✅ FEATURE #528 TEST PASSED!")
            print("="*70)
            print("\nFeature Validation:")
            print("  ✅ Step 1-4: Click 'Invite Member', enter email, select role, send invite")
            print("  ✅ Step 5: Email verification (auto-accepted for now)")
            print("  ✅ Step 6: User acceptance (auto-accepted for now)")
            print("  ✅ Step 7: Verified users added to team")
            print("  ✅ Duplicate invitation rejected correctly")
            print("  ✅ Invalid email rejected correctly")
            print("  ✅ Invalid role rejected correctly")
            print("  ✅ Non-admin invitation rejected correctly")
            return True
        else:
            print("\n❌ Some tests failed")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_feature_528_test()
    exit(0 if success else 1)
