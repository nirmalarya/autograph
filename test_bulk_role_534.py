#!/usr/bin/env python3
import requests

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

# Get the invitees we created earlier (they should have role 'user')
user_ids = [
    'invitee-1-533',
    'invitee-2-533',
    'invitee-3-533',
    'invitee-4-533',
    'invitee-5-533'
]

print(f"\n Testing bulk role change for {len(user_ids)} users...")
print("Changing roles from 'user' to 'admin'")

# Bulk change roles
headers = {"Authorization": f"Bearer {token}"}
role_change_data = {
    "user_ids": user_ids,
    "new_role": "admin"
}

response = requests.post(
    "http://localhost:8085/admin/users/bulk-role-change",
    headers=headers,
    json=role_change_data
)

print(f"\nBulk role change response: {response.status_code}")

if response.status_code != 200:
    print(f"✗ Bulk role change failed: {response.text}")
    exit(1)

result = response.json()
print(f"\n✓ Bulk role change successful!")
print(f"  Total users: {result['total']}")
print(f"  Successfully updated: {result['success_count']}")
print(f"  Failed: {result['failed_count']}")

if result['updated']:
    print(f"\n✓ Updated users:")
    for update in result['updated']:
        print(f"  - {update['email']}: {update['old_role']} → {update['new_role']}")

if result['failed']:
    print(f"\n⚠ Failed updates:")
    for fail in result['failed']:
        print(f"  - {fail.get('email', fail.get('user_id'))}: {fail['reason']}")

# Verify roles changed in database
import subprocess
print("\nVerifying roles in database...")
for i in range(1, 6):
    check_result = subprocess.run([
        'docker', 'exec', '-u', 'postgres', 'autograph-postgres',
        'psql', '-U', 'autograph', '-d', 'autograph', '-t', '-c',
        f"SELECT role FROM users WHERE id = 'invitee-{i}-533';"
    ], capture_output=True, text=True)

    role = check_result.stdout.strip()
    print(f"  User invitee-{i}-533: role = {role}")

if result['success_count'] == 5:
    print(f"\n✅ Feature #534: All {result['success_count']} user roles successfully changed!")
else:
    print(f"\n⚠ Only {result['success_count']}/5 users updated")
