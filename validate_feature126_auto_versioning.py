#!/usr/bin/env python3
"""
Feature #126: Update diagram with auto-versioning

Test Steps:
1. Create diagram (version 1)
2. Update diagram canvas_data
3. Send PUT /api/diagrams/<id>
4. Verify 200 OK response
5. Verify diagram updated
6. Check versions table
7. Verify version 2 created automatically
8. Verify version 2 contains snapshot of canvas_data
9. Verify version 1 still accessible
"""

import requests
import json
import sys
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Tuple

# Configuration
BASE_URL = "http://localhost:8080"
API_GATEWAY = f"{BASE_URL}/api"

def verify_email(email: str) -> None:
    """Verify user email in database."""
    verify_cmd = ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", f"UPDATE users SET is_verified = true WHERE email = '{email}';"]
    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Email verification may have failed: {result.stderr}")

def register_and_login(username_base: str) -> Tuple[str, str]:
    """Register a new user and return their JWT token and email"""
    # Use timestamp to create unique email
    email = f"{username_base.lower()}_{int(datetime.now().timestamp())}@test.com"
    password = "SecurePass123!"
    username = f"{username_base}_{int(datetime.now().timestamp())}"

    # Register
    register_response = requests.post(
        f"{API_GATEWAY}/auth/register",
        json={
            "email": email,
            "password": password,
            "username": username
        }
    )

    if register_response.status_code != 201:
        raise Exception(f"Registration failed: {register_response.text}")

    # Verify email in database
    verify_email(email)

    # Small delay to ensure DB update is committed
    time.sleep(1.0)

    # Login to get token
    login_response = requests.post(
        f"{API_GATEWAY}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    if login_response.status_code != 200:
        raise Exception(f"Failed to login after registration: {login_response.text}")

    return login_response.json()["access_token"], email

def create_diagram(token: str, title: str = "Versioning Test Diagram") -> Dict[str, Any]:
    """Create a new diagram and return the full response"""
    response = requests.post(
        f"{API_GATEWAY}/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {
                        "id": "shape1",
                        "type": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 100,
                        "text": "Version 1 Shape"
                    }
                ]
            }
        }
    )

    # Accept both 200 and 201 status codes
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create diagram: {response.status_code} - {response.text}")

    return response.json()

def update_diagram(token: str, diagram_id: str, new_canvas_data: Dict[str, Any]) -> requests.Response:
    """Update a diagram's canvas_data"""
    response = requests.put(
        f"{API_GATEWAY}/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "canvas_data": new_canvas_data
        }
    )
    return response

def get_diagram(token: str, diagram_id: str) -> requests.Response:
    """Get a diagram by ID"""
    response = requests.get(
        f"{API_GATEWAY}/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_diagram_versions(token: str, diagram_id: str) -> requests.Response:
    """Get all versions of a diagram"""
    response = requests.get(
        f"{API_GATEWAY}/diagrams/{diagram_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_specific_version(token: str, diagram_id: str, version_id: str) -> requests.Response:
    """Get a specific version of a diagram by version ID (UUID)"""
    response = requests.get(
        f"{API_GATEWAY}/diagrams/{diagram_id}/versions/{version_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def check_versions_in_db(diagram_id: str) -> str:
    """Check versions table in database"""
    check_cmd = [
        "docker", "exec", "autograph-postgres", "psql",
        "-U", "autograph", "-d", "autograph", "-c",
        f"SELECT version, created_at FROM diagram_versions WHERE diagram_id = '{diagram_id}' ORDER BY version;"
    ]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    return result.stdout

def run_test() -> bool:
    """Run the complete test"""
    print("=" * 80)
    print("Feature #126: Update diagram with auto-versioning")
    print("=" * 80)

    try:
        # Step 1: Create diagram (version 1)
        print("\n[Step 1] Create diagram (version 1)...")
        token, email = register_and_login("user_feature126")
        print(f"✓ User registered/logged in: {email}")

        initial_diagram = create_diagram(token, "Auto-Versioning Test")
        diagram_id = initial_diagram["id"]
        initial_version = initial_diagram.get("current_version", 1)
        print(f"✓ Diagram created: {diagram_id}")
        print(f"✓ Initial version: {initial_version}")
        print(f"✓ Initial canvas_data: {initial_diagram.get('canvas_data')}")

        # Step 2: Update diagram canvas_data
        print("\n[Step 2] Update diagram canvas_data...")
        new_canvas_data = {
            "shapes": [
                {
                    "id": "shape1",
                    "type": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "text": "Version 1 Shape"
                },
                {
                    "id": "shape2",
                    "type": "circle",
                    "x": 400,
                    "y": 200,
                    "radius": 50,
                    "text": "Version 2 - New Shape!"
                }
            ],
            "connections": [
                {
                    "from": "shape1",
                    "to": "shape2",
                    "type": "arrow"
                }
            ]
        }
        print(f"✓ Prepared new canvas_data with 2 shapes and 1 connection")

        # Step 3: Send PUT /api/diagrams/<id>
        print("\n[Step 3] Send PUT /api/diagrams/{id}...")
        update_response = update_diagram(token, diagram_id, new_canvas_data)
        print(f"✓ PUT request sent")

        # Step 4: Verify 200 OK response
        print("\n[Step 4] Verify 200 OK response...")
        if update_response.status_code != 200:
            print(f"✗ Expected 200 OK, got {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        print(f"✓ Received 200 OK")

        # Step 5: Verify diagram updated
        print("\n[Step 5] Verify diagram updated...")
        updated_diagram = update_response.json()
        updated_canvas = updated_diagram.get("canvas_data", {})

        if len(updated_canvas.get("shapes", [])) != 2:
            print(f"✗ Expected 2 shapes, got {len(updated_canvas.get('shapes', []))}")
            return False
        print(f"✓ Diagram now has 2 shapes")

        if len(updated_canvas.get("connections", [])) != 1:
            print(f"✗ Expected 1 connection, got {len(updated_canvas.get('connections', []))}")
            return False
        print(f"✓ Diagram now has 1 connection")

        new_version = updated_diagram.get("current_version")
        print(f"✓ Current version: {new_version}")

        # Step 6: Check versions table
        print("\n[Step 6] Check versions table in database...")
        db_versions = check_versions_in_db(diagram_id)
        print(f"Database versions:\n{db_versions}")

        # Step 7: Verify version 2 created automatically
        print("\n[Step 7] Verify version 2 created automatically...")
        versions_response = get_diagram_versions(token, diagram_id)

        if versions_response.status_code != 200:
            print(f"✗ Failed to get versions: {versions_response.status_code}")
            print(f"Response: {versions_response.text}")
            return False

        versions_data = versions_response.json()
        versions_list = versions_data.get("versions", [])

        if len(versions_list) < 2:
            print(f"✗ Expected at least 2 versions, got {len(versions_list)}")
            print(f"Versions: {versions_list}")
            return False
        print(f"✓ Found {len(versions_list)} versions in history")

        # Find version 2 and version 1 (API returns "version_number" field)
        version_1 = None
        version_2 = None
        for v in versions_list:
            if v.get("version_number") == 1:
                version_1 = v
            elif v.get("version_number") == 2:
                version_2 = v

        if not version_2:
            print(f"✗ Version 2 not found in versions list")
            print(f"   Available versions: {[v.get('version_number') for v in versions_list]}")
            return False
        print(f"✓ Version 2 found: {version_2.get('created_at')}")

        if not version_1:
            print(f"✗ Version 1 not found in versions list")
            return False

        # Step 8: Verify version 2 contains snapshot of canvas_data
        print("\n[Step 8] Verify version 2 contains snapshot of canvas_data...")
        version_2_id = version_2.get("id")
        version_2_response = get_specific_version(token, diagram_id, version_2_id)

        if version_2_response.status_code != 200:
            print(f"✗ Failed to get version 2: {version_2_response.status_code}")
            return False

        version_2_data = version_2_response.json()
        version_2_canvas = version_2_data.get("canvas_data", {})

        if len(version_2_canvas.get("shapes", [])) != 2:
            print(f"✗ Version 2 should have 2 shapes, got {len(version_2_canvas.get('shapes', []))}")
            return False
        print(f"✓ Version 2 has correct canvas_data (2 shapes)")

        # Check for the new shape
        shape_texts = [s.get("text", "") for s in version_2_canvas.get("shapes", [])]
        if "Version 2 - New Shape!" not in shape_texts:
            print(f"✗ Version 2 doesn't contain the new shape")
            return False
        print(f"✓ Version 2 contains the new shape")

        # Step 9: Verify version 1 still accessible
        print("\n[Step 9] Verify version 1 still accessible...")
        version_1_id = version_1.get("id")
        version_1_response = get_specific_version(token, diagram_id, version_1_id)

        if version_1_response.status_code != 200:
            print(f"✗ Failed to get version 1: {version_1_response.status_code}")
            return False
        print(f"✓ Version 1 is accessible")

        version_1_data = version_1_response.json()
        version_1_canvas = version_1_data.get("canvas_data", {})

        if len(version_1_canvas.get("shapes", [])) != 1:
            print(f"✗ Version 1 should have 1 shape, got {len(version_1_canvas.get('shapes', []))}")
            return False
        print(f"✓ Version 1 has original canvas_data (1 shape)")

        # Verify version 1 has the original shape
        v1_shape_texts = [s.get("text", "") for s in version_1_canvas.get("shapes", [])]
        if "Version 1 Shape" not in v1_shape_texts:
            print(f"✗ Version 1 doesn't contain the original shape")
            return False
        print(f"✓ Version 1 contains the original shape")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #126 working correctly!")
        print("=" * 80)
        print("\nSummary:")
        print("• Diagram created with version 1 ✓")
        print("• Diagram updated successfully (PUT 200 OK) ✓")
        print("• Version 2 created automatically ✓")
        print("• Version 2 contains updated canvas_data ✓")
        print("• Version 1 still accessible with original data ✓")
        print("• Auto-versioning system working correctly ✓")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
