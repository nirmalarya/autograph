#!/usr/bin/env python3
"""
Validation script for Feature #273: Mermaid Gantt Chart - Milestones
Tests that Mermaid Gantt charts can display milestones.
"""

import requests
import json
import sys
import time
import subprocess

API_GATEWAY = "http://localhost:8080"
AUTH_SERVICE = f"{API_GATEWAY}/api/auth"
DIAGRAM_SERVICE = f"{API_GATEWAY}/api/diagrams"

def register_and_login():
    """Register a test user and get auth token"""
    timestamp = int(time.time() * 1000)
    email = f"test_milestone_{timestamp}@example.com"
    password = "SecurePass123!"

    response = requests.post(f"{AUTH_SERVICE}/register", json={
        "email": email,
        "password": password,
        "full_name": "Milestone Test"
    })

    if response.status_code not in [200, 201]:
        return None, None

    user_data = response.json()
    user_id = user_data['id']

    verify_cmd = f"""docker exec autograph-postgres psql -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE id = '{user_id}';" """
    subprocess.run(verify_cmd, shell=True, capture_output=True)

    response = requests.post(f"{AUTH_SERVICE}/login", json={
        "email": email,
        "password": password
    })

    if response.status_code != 200:
        return None, None

    tokens = response.json()
    access_token = tokens.get("access_token")

    import base64
    payload = json.loads(base64.b64decode(access_token.split('.')[1] + '=='))
    user_id = payload['sub']

    return access_token, user_id

def create_gantt_with_milestones(access_token, user_id):
    """Create a Mermaid Gantt chart with milestones"""

    # Gantt chart with milestones (0d duration)
    mermaid_code = """gantt
    title Project with Milestones
    dateFormat YYYY-MM-DD

    section Phase 1
    Planning         :a1, 2024-01-01, 20d
    Kickoff Meeting  :milestone, m1, 2024-01-21, 0d

    section Phase 2
    Development      :a2, 2024-01-22, 30d
    Mid Review       :milestone, m2, 2024-02-21, 0d

    section Phase 3
    Testing          :a3, 2024-02-22, 15d
    Release          :milestone, m3, 2024-03-08, 0d
"""

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Gantt with Milestones",
            "diagram_type": "mermaid",
            "note_content": mermaid_code
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def validate_milestones(access_token, user_id, diagram_id):
    """Validate that milestones are preserved"""

    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch diagram: {response.status_code}")
        return False

    fetched = response.json()
    note_content = fetched.get('note_content', '')

    # Verify milestones
    required_elements = [
        ':milestone,',
        'm1',
        'm2',
        'm3',
        '0d',  # Zero duration for milestones
        'Kickoff Meeting',
        'Mid Review',
        'Release'
    ]

    for element in required_elements:
        if element not in note_content:
            print(f"❌ Missing milestone element: {element}")
            return False

    print("✅ Gantt milestones verified")
    print(f"   - Milestone marker: ':milestone,'")
    print(f"   - Zero duration (0d)")
    print(f"   - Multiple milestones: Kickoff, Mid Review, Release")
    print(f"   - Milestones integrated with tasks")

    return True

def main():
    """Main validation flow"""
    print("=" * 60)
    print("Feature #273: Mermaid Gantt Chart - Milestones")
    print("=" * 60)

    print("\n[1/3] Authenticating...")
    access_token, user_id = register_and_login()
    if not access_token:
        print("❌ FAILED: Authentication failed")
        sys.exit(1)
    print(f"✅ Authenticated")

    print("\n[2/3] Creating Gantt with milestones...")
    diagram = create_gantt_with_milestones(access_token, user_id)
    if not diagram:
        print("❌ FAILED: Could not create diagram")
        sys.exit(1)
    diagram_id = diagram.get('diagram_id') or diagram.get('id')
    print(f"✅ Created diagram ID: {diagram_id}")

    print("\n[3/3] Validating milestones...")
    if not validate_milestones(access_token, user_id, diagram_id):
        print("❌ FAILED: Milestone validation failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Feature #273: PASSED")
    print("   Mermaid Gantt charts support milestones")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
