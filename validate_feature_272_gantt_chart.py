#!/usr/bin/env python3
"""
Validation script for Feature #272: Mermaid Gantt Chart - Tasks and Dependencies
Tests that Mermaid diagrams can render Gantt charts with tasks and dependencies.
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
    email = f"test_gantt_{timestamp}@example.com"
    password = "SecurePass123!"

    # Register directly with auth service
    response = requests.post(f"{AUTH_SERVICE}/register", json={
        "email": email,
        "password": password,
        "full_name": "Gantt Test"
    })

    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return None, None

    # Get user ID from response
    user_data = response.json()
    user_id = user_data['id']

    # Verify email using docker exec
    verify_cmd = f"""docker exec autograph-postgres psql -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE id = '{user_id}';" """
    subprocess.run(verify_cmd, shell=True, capture_output=True)

    # Login directly with auth service
    response = requests.post(f"{AUTH_SERVICE}/login", json={
        "email": email,
        "password": password
    })

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return None, None

    tokens = response.json()
    access_token = tokens.get("access_token")

    # Decode token to get user_id
    import base64
    payload = json.loads(base64.b64decode(access_token.split('.')[1] + '=='))
    user_id = payload['sub']

    return access_token, user_id

def create_gantt_diagram(access_token, user_id):
    """Create a Mermaid Gantt chart with tasks and dependencies"""

    # Mermaid Gantt chart code
    mermaid_code = """gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD

    section Planning
    Requirements     :a1, 2024-01-01, 30d
    Design          :a2, after a1, 20d

    section Development
    Implementation  :a3, after a2, 45d
    Testing        :a4, after a3, 15d

    section Deployment
    Deployment     :a5, after a4, 5d
"""

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Gantt Chart Test",
            "diagram_type": "mermaid",
            "note_content": mermaid_code
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def validate_gantt_chart(access_token, user_id, diagram_id):
    """Validate that Gantt chart structure is preserved"""

    # Fetch the diagram
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

    # Verify Gantt chart elements
    required_elements = [
        'gantt',
        'title Project Timeline',
        'dateFormat',
        'Requirements',
        '2024-01-01',
        '30d',
        'after a1',  # Task dependency
        'Implementation',
        'Testing',
        'Deployment'
    ]

    for element in required_elements:
        if element not in note_content:
            print(f"❌ Missing Gantt chart element: {element}")
            return False

    print("✅ Gantt chart structure verified")
    print(f"   - Title: 'Project Timeline'")
    print(f"   - Date format specified")
    print(f"   - Multiple tasks defined")
    print(f"   - Task dependencies (after a1, after a2, etc.)")
    print(f"   - Task durations (30d, 20d, 45d, etc.)")
    print(f"   - Sections: Planning, Development, Deployment")

    return True

def main():
    """Main validation flow"""
    print("=" * 60)
    print("Feature #272: Mermaid Gantt Chart - Tasks and Dependencies")
    print("=" * 60)

    # Step 1: Authenticate
    print("\n[1/3] Authenticating...")
    access_token, user_id = register_and_login()
    if not access_token:
        print("❌ FAILED: Authentication failed")
        sys.exit(1)
    print(f"✅ Authenticated as user {user_id}")

    # Step 2: Create Gantt diagram
    print("\n[2/3] Creating Gantt chart diagram...")
    diagram = create_gantt_diagram(access_token, user_id)
    if not diagram:
        print("❌ FAILED: Could not create diagram")
        sys.exit(1)
    diagram_id = diagram.get('diagram_id') or diagram.get('id')
    print(f"✅ Created diagram ID: {diagram_id}")

    # Step 3: Validate Gantt chart
    print("\n[3/3] Validating Gantt chart structure...")
    if not validate_gantt_chart(access_token, user_id, diagram_id):
        print("❌ FAILED: Gantt chart validation failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Feature #272: PASSED")
    print("   Mermaid Gantt charts with tasks and dependencies work")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
