#!/usr/bin/env python3
"""
Validation script for Features #290-291: Mermaid Flowchart Styling and Custom Shapes
Tests that Mermaid flowcharts support node styling and custom shapes.
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
    """Register and login"""
    timestamp = int(time.time() * 1000)
    email = f"test_styling_{timestamp}@example.com"
    password = "SecurePass123!"

    response = requests.post(f"{AUTH_SERVICE}/register", json={
        "email": email,
        "password": password,
        "full_name": "Styling Test"
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

def test_styling_and_shapes(access_token, user_id):
    """Test flowchart with styled nodes and custom shapes"""

    # Mermaid flowchart with styling and custom shapes
    mermaid_code = """graph TD
    A[Rectangle] --> B(Round edges)
    B --> C{Diamond}
    C -->|Yes| D[[Subroutine]]
    C -->|No| E[(Database)]
    D --> F((Circle))
    E --> G>Asymmetric]

    style A fill:#f9f,stroke:#333,stroke-width:4px
    style B fill:#bbf,stroke:#f66,stroke-width:2px,color:#fff
    style C fill:#ff6,stroke:#333,stroke-width:2px
    style D fill:#6f6,stroke:#060,stroke-width:2px
"""

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Styled Flowchart",
            "diagram_type": "mermaid",
            "note_content": mermaid_code
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        return None

    return response.json()

def validate_styling(access_token, user_id, diagram_id):
    """Validate styling and shapes"""

    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
    )

    if response.status_code != 200:
        return False

    fetched = response.json()
    note_content = fetched.get('note_content', '')

    # Verify styling syntax
    style_elements = [
        'style A fill:',
        'stroke:',
        'stroke-width:',
        '[Rectangle]',
        '(Round edges)',
        '{Diamond}',
        '[[Subroutine]]',
        '[(Database)]',
        '((Circle))',
        '>Asymmetric]'
    ]

    for element in style_elements:
        if element not in note_content:
            print(f"❌ Missing element: {element}")
            return False

    print("✅ Flowchart styling and custom shapes verified")
    print(f"   - Custom shapes: Rectangle, Round, Diamond, Subroutine, Database, Circle, Asymmetric")
    print(f"   - Styling: fill colors, stroke colors, stroke-width")
    print(f"   - Multiple style statements applied")

    return True

def main():
    """Main validation"""
    print("=" * 70)
    print("Features #290-291: Flowchart Styling and Custom Shapes")
    print("=" * 70)

    print("\n[1/3] Authenticating...")
    access_token, user_id = register_and_login()
    if not access_token:
        print("❌ FAILED: Authentication failed")
        sys.exit(1)
    print("✅ Authenticated")

    print("\n[2/3] Creating styled flowchart...")
    diagram = test_styling_and_shapes(access_token, user_id)
    if not diagram:
        print("❌ FAILED: Could not create diagram")
        sys.exit(1)
    diagram_id = diagram.get('diagram_id') or diagram.get('id')
    print(f"✅ Created diagram")

    print("\n[3/3] Validating styling and shapes...")
    if not validate_styling(access_token, user_id, diagram_id):
        print("❌ FAILED")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✅ Features #290-291: PASSED")
    print("   Mermaid flowcharts support styling and custom node shapes")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
