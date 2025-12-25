#!/usr/bin/env python3
"""
Feature #160 Validation: Diagram version count display
Tests that version_count is properly tracked and displayed for diagrams.

Test Steps:
1. Register and login user
2. Create diagram (version 1) - verify version_count=1
3. Create 5 additional versions manually (versions 2-7) - verify version_count=7
4. View dashboard/list diagrams - verify version_count displayed
5. View version history - verify all 7 versions listed
6. Verify version_count persists across multiple requests
"""

import requests
import sys
import time
from datetime import datetime
import psycopg2

# Configuration
API_BASE_URL = "http://localhost:8080"  # API Gateway
DIAGRAM_SERVICE_URL = "http://localhost:8082"  # Direct to diagram service
AUTH_SERVICE_URL = "http://localhost:8085"  # Direct to auth service
UNIQUE_ID = datetime.now().strftime("%Y%m%d%H%M%S")

def print_step(step_num, description):
    """Print test step header."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def register_and_login():
    """Register a new user and login."""
    print_step(1, "Register and login user")

    # Register
    register_data = {
        "email": f"versiontest{UNIQUE_ID}@example.com",
        "password": "SecurePass123!",
        "username": f"versiontest{UNIQUE_ID}"
    }

    response = requests.post(f"{AUTH_SERVICE_URL}/register", json=register_data)
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    print("✅ User registered successfully")

    # Auto-verify email (for testing)
    user_data = response.json()
    user_id = user_data.get('user_id') or user_data.get('id')

    # Update user as verified in database
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="autograph",
            user="autograph",
            password="autograph_dev_password",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Email verified for user {user_id}")
    except Exception as e:
        print(f"❌ Failed to verify email: {e}")
        sys.exit(1)

    # Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }

    response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    token = response.json()["access_token"]
    print("✅ User logged in successfully")

    return token, user_id

def create_diagram(token, user_id):
    """Create a new diagram."""
    print_step(2, "Create diagram (version 1)")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    diagram_data = {
        "title": f"Version Count Test Diagram {UNIQUE_ID}",
        "file_type": "canvas",
        "canvas_data": {
            "nodes": [
                {"id": "node1", "type": "rectangle", "x": 100, "y": 100, "width": 100, "height": 50}
            ]
        }
    }

    response = requests.post(f"{DIAGRAM_SERVICE_URL}/", json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    diagram = response.json()
    diagram_id = diagram["id"]
    version_count = diagram.get("version_count", 0)
    current_version = diagram.get("current_version", 0)

    print(f"✅ Diagram created: {diagram_id}")
    print(f"   Current version: {current_version}")
    print(f"   Version count: {version_count}")

    # Verify initial version_count is 1
    if version_count != 1:
        print(f"❌ Expected version_count=1, got {version_count}")
        sys.exit(1)

    print("✅ Initial version_count is correct (1)")

    return diagram_id

def create_additional_versions(token, user_id, diagram_id, times=5):
    """Create additional versions manually."""
    print_step(3, f"Create {times} additional versions (creates versions 2-{times+1})")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # First, update the diagram to have different content for each version
    for i in range(times):
        # Update diagram content
        update_data = {
            "canvas_data": {
                "nodes": [
                    {"id": "node1", "type": "rectangle", "x": 100 + (i * 10), "y": 100, "width": 100, "height": 50},
                    {"id": f"node{i+2}", "type": "circle", "x": 200, "y": 200, "width": 80, "height": 80}
                ]
            }
        }

        response = requests.put(f"{DIAGRAM_SERVICE_URL}/{diagram_id}", json=update_data, headers=headers)
        if response.status_code != 200:
            print(f"❌ Update {i+1} failed: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        # Manually create a version snapshot
        version_data = {
            "description": f"Test version {i+2}",
            "label": f"v{i+2}"
        }

        response = requests.post(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", json=version_data, headers=headers)
        if response.status_code != 201:
            print(f"❌ Version creation {i+1} failed: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        version = response.json()
        version_number = version.get("version_number", 0)

        print(f"✅ Version {i+1} created - version_number={version_number}")

        time.sleep(0.1)  # Small delay between versions

    # Final verification
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get diagram: {response.status_code}")
        sys.exit(1)

    diagram = response.json()
    version_count = diagram.get("version_count", 0)
    # Note: We expect times + 2 because:
    # - 1 initial version on creation
    # - 1 auto-version on first PUT (due to auto-versioning)
    # - times manual versions
    expected_count = times + 2

    print(f"\nFinal version_count: {version_count} (expected: {expected_count})")

    if version_count != expected_count:
        print(f"❌ Expected version_count={expected_count}, got {version_count}")
        sys.exit(1)

    print(f"✅ Version count is correct: {version_count}")

    return version_count

def verify_dashboard_version_count(token, user_id, diagram_id):
    """Verify version_count is displayed in dashboard/list."""
    print_step(4, "View dashboard and verify version_count displayed")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Get list of diagrams
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get diagrams: {response.status_code}")
        sys.exit(1)

    response_data = response.json()

    # Handle both list and dict responses
    if isinstance(response_data, list):
        diagrams = response_data
    else:
        diagrams = response_data.get("diagrams", response_data.get("data", []))

    # Find our diagram
    our_diagram = None
    for diagram in diagrams:
        if diagram.get("id") == diagram_id:
            our_diagram = diagram
            break

    if not our_diagram:
        print(f"❌ Diagram not found in list")
        sys.exit(1)

    version_count = our_diagram.get("version_count")
    if version_count is None:
        print(f"❌ version_count not present in diagram response")
        sys.exit(1)

    print(f"✅ Diagram found in list with version_count: {version_count}")

    # Verify the count is correct (should be 7: 1 initial + 1 auto + 5 manual)
    if version_count != 7:
        print(f"❌ Expected version_count=7, got {version_count}")
        sys.exit(1)

    print(f"✅ version_count is correct in dashboard response")

    return True

def verify_version_history(token, user_id, diagram_id):
    """Verify version history shows all versions."""
    print_step(5, "View version history and verify all versions listed")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Get version history
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get version history: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    # Handle both list and dict responses
    if isinstance(response.json(), dict):
        versions = response.json().get("versions", [])
    else:
        versions = response.json()

    version_count = len(versions)

    print(f"✅ Retrieved version history: {version_count} versions")

    # Verify we have 7 versions
    if version_count != 7:
        print(f"❌ Expected 7 versions, got {version_count}")
        sys.exit(1)

    print(f"✅ All 7 versions are present in version history")

    # Display version numbers
    version_numbers = sorted([v.get("version_number", 0) for v in versions])
    print(f"   Version numbers: {version_numbers}")

    if version_numbers != [1, 2, 3, 4, 5, 6, 7]:
        print(f"❌ Version numbers are not sequential: {version_numbers}")
        sys.exit(1)

    print(f"✅ Version numbers are sequential and correct")

    return versions

def verify_version_count_persistence(token, user_id, diagram_id):
    """Verify version_count persists across requests."""
    print_step(6, "Verify version_count persists across multiple requests")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Get diagram multiple times to verify count is consistent
    for i in range(3):
        response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}", headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get diagram (attempt {i+1}): {response.status_code}")
            sys.exit(1)

        diagram = response.json()
        version_count = diagram.get("version_count", 0)

        if version_count != 7:
            print(f"❌ version_count changed unexpectedly: got {version_count}, expected 7")
            sys.exit(1)

        print(f"✅ Request {i+1}: version_count is 7 (consistent)")
        time.sleep(0.2)

    print(f"✅ version_count persists correctly across multiple requests")

    return True

def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("FEATURE #160 VALIDATION: Diagram Version Count Display")
    print("="*60)

    try:
        # Step 1: Register and login
        token, user_id = register_and_login()

        # Step 2: Create diagram (version 1)
        diagram_id = create_diagram(token, user_id)

        # Step 3: Create 5 additional versions
        create_additional_versions(token, user_id, diagram_id, times=5)

        # Step 4: Verify dashboard shows version_count
        verify_dashboard_version_count(token, user_id, diagram_id)

        # Step 5: Verify version history
        versions = verify_version_history(token, user_id, diagram_id)

        # Step 6: Verify version_count persistence
        verify_version_count_persistence(token, user_id, diagram_id)

        # Final success
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nFeature #160 validation completed successfully!")
        print("- version_count starts at 1")
        print("- version_count increments when versions created")
        print("- version_count displayed in dashboard/list")
        print("- version_count shown in version history")
        print("- version_count persists correctly across requests")
        print("- Database triggers working correctly")
        print(f"- Final count: 7 versions (1 initial + 1 auto + 5 manual)")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
