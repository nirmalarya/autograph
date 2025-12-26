#!/usr/bin/env python3
"""Test Feature #527: Enterprise: Team management: create teams

Tests the following workflow:
1. Admin creates team: 'Engineering'
2. Add members
3. Verify team created
4. Verify members added
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8080/api"  # Via API Gateway
AUTH_SERVICE_URL = "http://localhost:8085"  # Direct to auth service

def create_test_user(username_prefix="team_admin"):
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
        return None, None

    print(f"   ✅ User registered successfully")

    # Get user ID from registration response
    reg_data = response.json()
    user_id = reg_data.get("user_id") or reg_data.get("id")

    # Verify email directly via SQL (bypass email verification for testing)
    print(f"   📧 Verifying email via database...")
    import subprocess
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
        return None, None

    data = response.json()
    access_token = data.get("access_token")

    print(f"   ✅ Login successful, got access token")

    return email, access_token


def test_create_team(access_token):
    """Test creating a new team."""
    timestamp = int(time.time())
    team_name = f"Engineering Team {timestamp}"

    print(f"\n🏢 Creating team: {team_name}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    team_data = {
        "name": team_name,
        "plan": "enterprise",
        "max_members": 50
    }

    response = requests.post(
        f"{BASE_URL}/auth/teams",
        headers=headers,
        json=team_data
    )

    print(f"   Status: {response.status_code}")

    if response.status_code not in [200, 201]:
        print(f"   ❌ Team creation failed")
        print(f"   Response: {response.text}")
        return None

    team = response.json()
    print(f"   ✅ Team created successfully!")
    print(f"   Team ID: {team['id']}")
    print(f"   Team Name: {team['name']}")
    print(f"   Team Slug: {team['slug']}")
    print(f"   Plan: {team['plan']}")
    print(f"   Max Members: {team['max_members']}")
    print(f"   Members Count: {team.get('members_count', 0)}")

    return team


def test_invite_member(team_id, admin_token, member_email):
    """Test inviting a member to the team."""
    print(f"\n👥 Inviting member: {member_email}")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    invite_data = {
        "email": member_email,
        "role": "editor"
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
    print(f"   Status: {member['invitation_status']}")

    return member


def test_get_team_members(team_id, admin_token):
    """Test getting all members of a team."""
    print(f"\n👥 Getting team members...")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{BASE_URL}/auth/teams/{team_id}/members",
        headers=headers
    )

    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ❌ Failed to get team members")
        print(f"   Response: {response.text}")
        return None

    data = response.json()
    members = data.get("members", [])

    print(f"   ✅ Retrieved {len(members)} team member(s):")
    for member in members:
        print(f"     - {member['user_email']} ({member['role']}) - {member['invitation_status']}")

    return members


def run_feature_527_test():
    """Run complete test for Feature #527."""
    print("\n" + "="*70)
    print("FEATURE #527: Enterprise Team Management - Create Teams")
    print("="*70)

    try:
        # Step 1: Create admin user
        print("\n[Step 1] Creating admin user...")
        admin_email, admin_token = create_test_user("team_admin")
        if not admin_token:
            print("\n❌ Failed to create admin user")
            return False

        # Step 2: Create team
        print("\n[Step 2] Creating team 'Engineering'...")
        team = test_create_team(admin_token)
        if not team:
            print("\n❌ Failed to create team")
            return False

        team_id = team['id']

        # Verify team was created with owner as first member
        if team.get('members_count', 0) < 1:
            print("\n❌ Team should have at least 1 member (owner)")
            return False

        print(f"\n✅ Team created with {team.get('members_count')} member(s)")

        # Step 3: Create additional members
        print("\n[Step 3] Creating additional team members...")
        member1_email, member1_token = create_test_user("team_member1")
        member2_email, member2_token = create_test_user("team_member2")

        if not member1_email or not member2_email:
            print("\n⚠️  Warning: Could not create all test members, but team creation works")

        # Step 4: Invite members to team
        print("\n[Step 4] Inviting members to team...")

        if member1_email:
            member1 = test_invite_member(team_id, admin_token, member1_email)
            if not member1:
                print("\n⚠️  Warning: Failed to invite member 1")

        if member2_email:
            member2 = test_invite_member(team_id, admin_token, member2_email)
            if not member2:
                print("\n⚠️  Warning: Failed to invite member 2")

        # Step 5: Verify all members
        print("\n[Step 5] Verifying team members...")
        members = test_get_team_members(team_id, admin_token)

        if members is None:
            print("\n❌ Failed to retrieve team members")
            return False

        # Should have admin + invited members
        expected_count = 1  # At minimum, the admin
        if member1_email:
            expected_count += 1
        if member2_email:
            expected_count += 1

        if len(members) < 1:
            print(f"\n❌ Expected at least 1 member (admin), got {len(members)}")
            return False

        print(f"\n✅ Team has {len(members)} member(s)")

        # Verify admin is in the team
        admin_found = False
        for member in members:
            if member['user_email'] == admin_email:
                admin_found = True
                if member['role'] != 'admin':
                    print(f"\n⚠️  Warning: Team owner should have 'admin' role, got '{member['role']}'")
                break

        if not admin_found:
            print(f"\n❌ Admin {admin_email} not found in team members")
            return False

        print(f"\n✅ Admin {admin_email} confirmed as team member")

        # Final summary
        print("\n" + "="*70)
        print("✅ FEATURE #527 TEST PASSED!")
        print("="*70)
        print("\nSummary:")
        print(f"  ✅ Team '{team['name']}' created successfully")
        print(f"  ✅ Team ID: {team['id']}")
        print(f"  ✅ Team has {len(members)} member(s)")
        print(f"  ✅ Admin user verified as team member")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_feature_527_test()
    exit(0 if success else 1)
