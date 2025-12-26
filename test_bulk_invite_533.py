#!/usr/bin/env python3
import requests
import bcrypt
import subprocess

# First, create a test team
print("Setting up test environment...")

# Create team owner
owner_hash = bcrypt.hashpw(b'testpass123', bcrypt.gensalt()).decode()
subprocess.run([
    'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-c',
    f"INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at) VALUES ('team-owner-533', 'teamowner533@example.com', '{owner_hash}', 'Team Owner', 'user', true, true, NOW(), NOW()) ON CONFLICT (email) DO UPDATE SET password_hash = '{owner_hash}';"
], capture_output=True, text=True)

# Create a team
subprocess.run([
    'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-c',
    "INSERT INTO teams (id, name, owner_id, created_at, updated_at) VALUES ('team-533-test', 'Test Team 533', 'team-owner-533', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;"
], capture_output=True, text=True)

# Create 5 test users to invite
for i in range(1, 6):
    user_hash = bcrypt.hashpw(b'testpass123', bcrypt.gensalt()).decode()
    subprocess.run([
        'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
        'psql', '-U', 'autograph', '-d', 'autograph', '-c',
        f"INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at) VALUES ('invitee-{i}-533', 'invitee{i}@example.com', '{user_hash}', 'Invitee {i}', 'user', true, true, NOW(), NOW()) ON CONFLICT (email) DO UPDATE SET password_hash = '{user_hash}';"
    ], capture_output=True, text=True)
    print(f"✓ Created user: invitee{i}@example.com")

# Make admin user a team admin
subprocess.run([
    'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-c',
    "INSERT INTO team_members (id, team_id, user_id, role, invitation_status, invited_by, invitation_sent_at, invitation_accepted_at) VALUES ('admin-member-533', 'team-533-test', 'admin-532-test', 'admin', 'active', 'team-owner-533', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;"
], capture_output=True, text=True)

print("\n✓ Test environment ready")
print("\nTesting bulk invite...")

# Login as admin
login_response = requests.post(
    "http://localhost:8085/login",
    json={"email": "admin532@example.com", "password": "testpass123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
print("✓ Admin login successful")

# Bulk invite users to team
headers = {"Authorization": f"Bearer {token}"}
bulk_invite_data = {
    "emails": [
        "invitee1@example.com",
        "invitee2@example.com",
        "invitee3@example.com",
        "invitee4@example.com",
        "invitee5@example.com"
    ],
    "role": "viewer",
    "team_id": "team-533-test"
}

invite_response = requests.post(
    "http://localhost:8085/admin/users/bulk-invite",
    headers=headers,
    json=bulk_invite_data
)

print(f"\nBulk invite response: {invite_response.status_code}")

if invite_response.status_code != 200:
    print(f"✗ Bulk invite failed: {invite_response.text}")
    exit(1)

result = invite_response.json()
print(f"\n✓ Bulk invite successful!")
print(f"  Total emails: {result['total']}")
print(f"  Successfully invited: {result['success_count']}")
print(f"  Failed: {result['failed_count']}")

if result['invited']:
    print(f"\n✓ Invited users:")
    for inv in result['invited']:
        print(f"  - {inv['email']} (role: {inv['role']})")

if result['failed']:
    print(f"\n⚠ Failed invitations:")
    for fail in result['failed']:
        print(f"  - {fail['email']}: {fail['reason']}")

# Verify all users were invited
if result['success_count'] == 5:
    print(f"\n✅ Feature #533: All {result['success_count']} users successfully invited!")
else:
    print(f"\n⚠ Only {result['success_count']}/5 users invited")

# Verify team membership
print("\nVerifying team membership...")
check_result = subprocess.run([
    'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
    'psql', '-U', 'autograph', '-d', 'autograph', '-t', '-c',
    "SELECT COUNT(*) FROM team_members WHERE team_id = 'team-533-test' AND user_id LIKE 'invitee-%';"
], capture_output=True, text=True)

member_count = int(check_result.stdout.strip())
print(f"✓ Team members in database: {member_count}")

if member_count == 5:
    print("\n✅ Feature #533: Bulk invite - PASSING")
else:
    print(f"\n⚠ Expected 5 members, found {member_count}")
