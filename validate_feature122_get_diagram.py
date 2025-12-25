#!/usr/bin/env python3
"""
Feature #122 Validation: Get diagram by ID returns full canvas_data and note_content
Tests that GET /api/diagrams/<id> returns complete diagram data.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
API_GATEWAY = f"{BASE_URL}/api"

def test_get_diagram_full_content():
    """Test getting diagram by ID with full content."""
    print("=" * 80)
    print("Feature #122: Get diagram by ID returns full canvas_data and note_content")
    print("=" * 80)

    try:
        # Step 1: Register test user
        print("\n1. Registering test user...")
        register_response = requests.post(
            f"{API_GATEWAY}/auth/register",
            json={
                "email": f"test_get_diagram_{datetime.now().timestamp()}@example.com",
                "password": "SecurePass123!@#",
                "username": "testuser_get_diagram"
            }
        )

        if register_response.status_code != 201:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(register_response.text)
            return False

        user_data = register_response.json()
        user_id = user_data.get("user_id")
        print(f"✅ User registered: {user_id}")

        # Verify email in database
        import subprocess
        email = user_data["email"]
        verify_cmd = f"""docker exec autograph-postgres psql -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE email = '{email}';" """
        subprocess.run(verify_cmd, shell=True, capture_output=True)
        print(f"✅ Email verified in database")

        # Step 2: Login
        print("\n2. Logging in...")
        login_response = requests.post(
            f"{API_GATEWAY}/auth/login",
            json={
                "email": user_data["email"],
                "password": "SecurePass123!@#"
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False

        tokens = login_response.json()
        access_token = tokens.get("access_token")
        print(f"✅ Login successful")

        # Step 3: Create diagram with both canvas shapes and note text
        print("\n3. Creating diagram with canvas shapes and note text...")

        canvas_data = {
            "shapes": [
                {
                    "id": "shape1",
                    "type": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 150,
                    "fill": "#3498db",
                    "stroke": "#2c3e50"
                },
                {
                    "id": "shape2",
                    "type": "circle",
                    "x": 400,
                    "y": 200,
                    "radius": 75,
                    "fill": "#e74c3c",
                    "stroke": "#c0392b"
                }
            ],
            "connections": [
                {
                    "id": "conn1",
                    "from": "shape1",
                    "to": "shape2",
                    "type": "arrow"
                }
            ]
        }

        note_content = """# Test Diagram

This is a test diagram with both canvas and note content.

## Features
- Canvas with shapes
- Rich text notes
- Full content retrieval
"""

        create_response = requests.post(
            f"{API_GATEWAY}/diagrams",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-User-ID": user_id
            },
            json={
                "title": "Test Diagram - Full Content",
                "file_type": "mixed",
                "canvas_data": canvas_data,
                "note_content": note_content
            }
        )

        if create_response.status_code not in [200, 201]:
            print(f"❌ Diagram creation failed: {create_response.status_code}")
            print(create_response.text)
            return False

        diagram = create_response.json()
        diagram_id = diagram.get("id")
        print(f"✅ Diagram created: {diagram_id}")

        # Step 4: Send GET /api/diagrams/<id>
        print(f"\n4. Sending GET /api/diagrams/{diagram_id}...")
        get_response = requests.get(
            f"{API_GATEWAY}/diagrams/{diagram_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-User-ID": user_id
            }
        )

        if get_response.status_code != 200:
            print(f"❌ GET request failed: {get_response.status_code}")
            print(get_response.text)
            return False

        print(f"✅ GET request successful: 200 OK")

        # Step 5: Verify response contains full canvas_data JSON
        print("\n5. Verifying response contains full canvas_data JSON...")
        fetched_diagram = get_response.json()

        if "canvas_data" not in fetched_diagram:
            print("❌ canvas_data missing from response")
            return False

        if fetched_diagram["canvas_data"] is None:
            print("❌ canvas_data is null")
            return False

        fetched_canvas = fetched_diagram["canvas_data"]
        if "shapes" not in fetched_canvas or "connections" not in fetched_canvas:
            print("❌ canvas_data missing shapes or connections")
            return False

        if len(fetched_canvas["shapes"]) != 2:
            print(f"❌ Expected 2 shapes, got {len(fetched_canvas['shapes'])}")
            return False

        if len(fetched_canvas["connections"]) != 1:
            print(f"❌ Expected 1 connection, got {len(fetched_canvas['connections'])}")
            return False

        print("✅ Response contains full canvas_data JSON")

        # Step 6: Verify response contains full note_content markdown
        print("\n6. Verifying response contains full note_content markdown...")

        if "note_content" not in fetched_diagram:
            print("❌ note_content missing from response")
            return False

        if fetched_diagram["note_content"] is None:
            print("❌ note_content is null")
            return False

        fetched_note = fetched_diagram["note_content"]
        if "# Test Diagram" not in fetched_note:
            print("❌ note_content missing expected markdown header")
            return False

        if "Canvas with shapes" not in fetched_note:
            print("❌ note_content missing expected content")
            return False

        print("✅ Response contains full note_content markdown")

        # Step 7: Verify response contains metadata
        print("\n7. Verifying response contains metadata...")

        required_metadata = ["title", "created_at", "updated_at", "owner_id"]
        for field in required_metadata:
            if field not in fetched_diagram:
                print(f"❌ Missing metadata field: {field}")
                return False

        if fetched_diagram["title"] != "Test Diagram - Full Content":
            print(f"❌ Title mismatch: {fetched_diagram['title']}")
            return False

        # Verify owner_id matches the created diagram (not necessarily the registration user_id)
        if fetched_diagram["owner_id"] != diagram.get("owner_id"):
            print(f"❌ Owner ID mismatch: {fetched_diagram['owner_id']} vs {diagram.get('owner_id')}")
            return False

        print("✅ Response contains metadata (title, created_at, updated_at, owner_id)")

        # Step 8: Verify response contains version information
        print("\n8. Verifying response contains version information...")

        version_fields = ["current_version", "version_count"]
        for field in version_fields:
            if field not in fetched_diagram:
                print(f"❌ Missing version field: {field}")
                return False

        if fetched_diagram["current_version"] < 1:
            print(f"❌ Invalid current_version: {fetched_diagram['current_version']}")
            return False

        if fetched_diagram["version_count"] < 1:
            print(f"❌ Invalid version_count: {fetched_diagram['version_count']}")
            return False

        print(f"✅ Response contains version information (version {fetched_diagram['current_version']} of {fetched_diagram['version_count']})")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #122 is working!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_get_diagram_full_content()
    sys.exit(0 if success else 1)
