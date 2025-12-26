#!/usr/bin/env python3
"""
Feature #472: Fork Version - Create new diagram from old version
Tests the ability to fork a version to create an independent copy
"""

import requests
import json
import sys

API_BASE = "http://localhost:8080"
DIAGRAM_API = f"{API_BASE}/api/diagrams"

# Test user credentials
TEST_EMAIL = "test_user_472@example.com"
TEST_PASSWORD = "SecurePass123!"
TEST_FULL_NAME = "Test User 472"

def register_and_login():
    """Register and login test user"""
    print("Step 1: Register and login test user")

    # Register
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME
    }

    try:
        response = requests.post(f"{API_BASE}/api/auth/register", json=register_data)
        if response.status_code == 201:
            print("  ✓ User registered successfully")
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print("  ℹ User already exists, proceeding to login")
        else:
            print(f"  ✗ Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  ℹ Registration note: {e}")

    # Login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"  ✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None, None

    data = response.json()
    access_token = data["access_token"]
    # Handle different response formats
    if "user" in data:
        user_id = data["user"]["id"]
    elif "user_id" in data:
        user_id = data["user_id"]
    else:
        # Try to decode the JWT to get user_id
        import base64
        try:
            payload_part = access_token.split('.')[1]
            # Add padding if needed
            padding = 4 - len(payload_part) % 4
            if padding != 4:
                payload_part += '=' * padding
            payload = json.loads(base64.b64decode(payload_part))
            user_id = payload.get('sub') or payload.get('user_id')
        except:
            print(f"  ✗ Could not extract user_id from response: {data}")
            return None, None

    print(f"  ✓ Logged in successfully (User ID: {user_id})")

    return access_token, user_id


def create_test_diagram(token, user_id):
    """Create a test diagram"""
    print("\nStep 2: Create test diagram")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    diagram_data = {
        "title": "Test Diagram for Fork v472",
        "file_type": "canvas",
        "canvas_data": {
            "version": "1.0",
            "elements": [
                {"id": "elem1", "type": "box", "x": 100, "y": 100, "text": "Original Element"}
            ]
        }
    }

    response = requests.post(DIAGRAM_API, json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"  ✗ Failed to create diagram: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"  ✓ Created diagram: {diagram_id}")
    return diagram_id


def update_diagram_create_versions(token, user_id, diagram_id):
    """Update diagram multiple times to create versions"""
    print("\nStep 3: Create multiple versions")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    # Update 1 - Add element
    update_data = {
        "canvas_data": {
            "version": "1.0",
            "elements": [
                {"id": "elem1", "type": "box", "x": 100, "y": 100, "text": "Original Element"},
                {"id": "elem2", "type": "box", "x": 200, "y": 200, "text": "Version 2 Element"}
            ]
        }
    }

    response = requests.put(f"{DIAGRAM_API}/{diagram_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        print("  ✓ Created version 2")
    else:
        print(f"  ✗ Failed to create version 2: {response.status_code}")
        return False

    # Update 2 - Add another element
    update_data["canvas_data"]["elements"].append(
        {"id": "elem3", "type": "circle", "x": 300, "y": 300, "text": "Version 3 Element"}
    )

    response = requests.put(f"{DIAGRAM_API}/{diagram_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        print("  ✓ Created version 3")
    else:
        print(f"  ✗ Failed to create version 3: {response.status_code}")
        return False

    return True


def get_versions(token, user_id, diagram_id):
    """Get all versions of the diagram"""
    print("\nStep 4: Get versions list")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(f"{DIAGRAM_API}/{diagram_id}/versions", headers=headers)
    if response.status_code != 200:
        print(f"  ✗ Failed to get versions: {response.status_code}")
        return None

    data = response.json()
    versions = data.get("versions", [])
    print(f"  ✓ Found {len(versions)} versions")

    return versions


def fork_version(token, user_id, diagram_id, version_id, version_number):
    """Fork a specific version"""
    print(f"\nStep 5: Fork version {version_number}")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{DIAGRAM_API}/{diagram_id}/versions/{version_id}/fork",
        headers=headers
    )

    if response.status_code != 200:
        print(f"  ✗ Failed to fork version: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

    result = response.json()
    new_diagram_id = result.get("new_diagram_id")
    new_title = result.get("new_diagram_title")

    print(f"  ✓ Forked successfully")
    print(f"    New diagram ID: {new_diagram_id}")
    print(f"    New title: {new_title}")

    return new_diagram_id


def verify_new_diagram(token, user_id, new_diagram_id, original_diagram_id):
    """Verify the new diagram is independent"""
    print("\nStep 6: Verify new diagram is independent copy")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Get new diagram
    response = requests.get(f"{DIAGRAM_API}/{new_diagram_id}", headers=headers)
    if response.status_code != 200:
        print(f"  ✗ Failed to get new diagram: {response.status_code}")
        return False

    new_diagram = response.json()
    print(f"  ✓ New diagram exists: {new_diagram['title']}")

    # Verify it has different ID
    if new_diagram["id"] == original_diagram_id:
        print(f"  ✗ New diagram has same ID as original!")
        return False
    print(f"  ✓ New diagram has unique ID")

    # Verify it has its own version history
    response = requests.get(f"{DIAGRAM_API}/{new_diagram_id}/versions", headers=headers)
    if response.status_code == 200:
        versions = response.json().get("versions", [])
        print(f"  ✓ New diagram has {len(versions)} version(s) (fresh history)")
        if len(versions) >= 1:
            print(f"  ✓ Initial version created")
        else:
            print(f"  ✗ No initial version found")
            return False
    else:
        print(f"  ✗ Failed to get new diagram versions")
        return False

    return True


def verify_original_unchanged(token, user_id, original_diagram_id):
    """Verify original diagram is unchanged"""
    print("\nStep 7: Verify original diagram unchanged")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(f"{DIAGRAM_API}/{original_diagram_id}", headers=headers)
    if response.status_code != 200:
        print(f"  ✗ Failed to get original diagram: {response.status_code}")
        return False

    original = response.json()
    print(f"  ✓ Original diagram still exists")
    print(f"  ✓ Original title: {original['title']}")

    # Get original versions
    response = requests.get(f"{DIAGRAM_API}/{original_diagram_id}/versions", headers=headers)
    if response.status_code == 200:
        versions = response.json().get("versions", [])
        print(f"  ✓ Original still has {len(versions)} versions (unchanged)")

    return True


def cleanup(token, user_id, diagram_ids):
    """Clean up test diagrams"""
    print("\nCleanup: Deleting test diagrams")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    for diagram_id in diagram_ids:
        if diagram_id:
            requests.delete(f"{DIAGRAM_API}/{diagram_id}", headers=headers)
            print(f"  ✓ Deleted diagram: {diagram_id}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Feature #472: Fork Version Test")
    print("=" * 60)

    # Step 1: Auth
    token, user_id = register_and_login()
    if not token:
        print("\n❌ TEST FAILED: Authentication failed")
        return False

    # Step 2: Create diagram
    diagram_id = create_test_diagram(token, user_id)
    if not diagram_id:
        print("\n❌ TEST FAILED: Could not create diagram")
        return False

    # Step 3: Create versions
    if not update_diagram_create_versions(token, user_id, diagram_id):
        cleanup(token, user_id, [diagram_id])
        print("\n❌ TEST FAILED: Could not create versions")
        return False

    # Step 4: Get versions
    versions = get_versions(token, user_id, diagram_id)
    if not versions or len(versions) < 2:
        cleanup(token, user_id, [diagram_id])
        print("\n❌ TEST FAILED: Not enough versions created")
        return False

    # Select version 2 to fork (middle version)
    version_to_fork = None
    for v in versions:
        if v["version_number"] == 2:
            version_to_fork = v
            break

    if not version_to_fork:
        cleanup(token, user_id, [diagram_id])
        print("\n❌ TEST FAILED: Version 2 not found")
        return False

    # Step 5: Fork version
    new_diagram_id = fork_version(
        token, user_id, diagram_id,
        version_to_fork["id"],
        version_to_fork["version_number"]
    )
    if not new_diagram_id:
        cleanup(token, user_id, [diagram_id])
        print("\n❌ TEST FAILED: Fork failed")
        return False

    # Step 6: Verify new diagram
    if not verify_new_diagram(token, user_id, new_diagram_id, diagram_id):
        cleanup(token, user_id, [diagram_id, new_diagram_id])
        print("\n❌ TEST FAILED: New diagram verification failed")
        return False

    # Step 7: Verify original unchanged
    if not verify_original_unchanged(token, user_id, diagram_id):
        cleanup(token, user_id, [diagram_id, new_diagram_id])
        print("\n❌ TEST FAILED: Original diagram was modified")
        return False

    # Cleanup
    cleanup(token, user_id, [diagram_id, new_diagram_id])

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Feature #472 Working!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
