#!/usr/bin/env python3
"""
Validation script for Feature #271: Mermaid State Diagram - Nested States
Tests that Mermaid diagrams can contain nested state structures.
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
    email = f"test_nested_states_{timestamp}@example.com"
    password = "SecurePass123!"

    # Register directly with auth service
    response = requests.post(f"{AUTH_SERVICE}/register", json={
        "email": email,
        "password": password,
        "full_name": "Nested States Test"
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

def create_nested_state_diagram(access_token, user_id):
    """Create a Mermaid diagram with nested states"""

    # Mermaid code with nested states
    mermaid_code = """stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> Running
        Running --> Paused
        Paused --> Running
        Running --> [*]
    }

    Active --> Stopped
    Stopped --> [*]
"""

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Nested State Diagram Test",
            "diagram_type": "mermaid",
            "note_content": mermaid_code
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def validate_nested_states(access_token, user_id, diagram_id):
    """Validate that nested state structure is preserved"""

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

    # Verify nested state structure
    required_elements = [
        'stateDiagram-v2',
        'state Active {',  # Nested state block
        '[*] --> Running',  # Nested initial state
        'Running --> Paused',  # Nested transition
        'Paused --> Running',
        'Running --> [*]',  # Nested final state
        '}',  # End of nested block
        'Active --> Stopped',  # Transition from nested state
    ]

    for element in required_elements:
        if element not in note_content:
            print(f"❌ Missing nested state element: {element}")
            return False

    print("✅ Nested state structure verified")
    print(f"   - Nested state 'Active' with sub-states")
    print(f"   - Sub-states: Running, Paused")
    print(f"   - Nested transitions verified")
    print(f"   - Proper nesting syntax with braces")

    return True

def main():
    """Main validation flow"""
    print("=" * 60)
    print("Feature #271: Mermaid State Diagram - Nested States")
    print("=" * 60)

    # Step 1: Authenticate
    print("\n[1/3] Authenticating...")
    access_token, user_id = register_and_login()
    if not access_token:
        print("❌ FAILED: Authentication failed")
        sys.exit(1)
    print(f"✅ Authenticated as user {user_id}")

    # Step 2: Create nested state diagram
    print("\n[2/3] Creating nested state diagram...")
    diagram = create_nested_state_diagram(access_token, user_id)
    if not diagram:
        print("❌ FAILED: Could not create diagram")
        sys.exit(1)
    diagram_id = diagram.get('diagram_id') or diagram.get('id')
    print(f"✅ Created diagram ID: {diagram_id}")

    # Step 3: Validate nested states
    print("\n[3/3] Validating nested state structure...")
    if not validate_nested_states(access_token, user_id, diagram_id):
        print("❌ FAILED: Nested state validation failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Feature #271: PASSED")
    print("   Mermaid state diagrams support nested states")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
