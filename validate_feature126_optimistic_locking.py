#!/usr/bin/env python3
"""
Feature #127: Optimistic Locking for Diagram Updates
Tests that concurrent updates are prevented using version numbers.

Test Steps:
1. User A fetches diagram (version 5)
2. User B fetches diagram (version 5)
3. User A updates diagram (version 6)
4. User B attempts to update with version 5
5. Verify 409 Conflict response
6. Verify error: 'Diagram was modified by another user'
7. User B refetches diagram (version 6)
8. User B updates successfully (version 7)
"""

import requests
import json
import sys
import time
import psycopg2

# Configuration
API_GATEWAY = "http://localhost:8080"
AUTH_API = f"{API_GATEWAY}/api/auth"
DIAGRAM_API = f"{API_GATEWAY}/api/diagrams"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def register_and_login_user(email, password, full_name):
    """Register and login a user, return access token."""
    # Register
    register_data = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    response = requests.post(f"{AUTH_API}/register", json=register_data)
    if response.status_code != 201:
        print(f"❌ Registration failed for {email}: {response.text}")
        return None

    # Mark user as verified (skip email verification for test)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to verify user {email}: {e}")
        return None

    # Login
    login_data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{AUTH_API}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed for {email}: {response.text}")
        return None

    data = response.json()
    return data.get("access_token")

def create_diagram(token):
    """Create a diagram for testing."""
    headers = {"Authorization": f"Bearer {token}"}

    # Create initial diagram (version 1)
    create_data = {
        "title": "Optimistic Locking Test Diagram",
        "file_type": "canvas",
        "canvas_data": {
            "shapes": [
                {"id": "shape1", "type": "rectangle", "x": 0, "y": 0}
            ]
        }
    }

    response = requests.post(DIAGRAM_API, json=create_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram (status {response.status_code}): {response.text}")
        return None, None

    data = response.json()
    diagram_id = data.get("id")
    current_version = data.get("current_version", 1)

    return diagram_id, current_version

def main():
    """Main test execution."""
    print("=" * 80)
    print("Feature #127: Optimistic Locking for Diagram Updates")
    print("=" * 80)
    print()

    # Step 1: Register and login User A and User B
    print("Step 1: Setting up users...")
    user_a_email = f"user_a_optlock_{int(time.time())}@test.com"
    user_b_email = f"user_b_optlock_{int(time.time())}@test.com"
    password = "SecurePass123!"

    token_a = register_and_login_user(user_a_email, password, "User A")
    if not token_a:
        print("❌ Failed to setup User A")
        return False

    token_b = register_and_login_user(user_b_email, password, "User B")
    if not token_b:
        print("❌ Failed to setup User B")
        return False

    print(f"✅ User A registered: {user_a_email}")
    print(f"✅ User B registered: {user_b_email}")
    print()

    # Step 2: User A creates a diagram
    print("Step 2: User A creates diagram...")
    diagram_id, initial_version = create_diagram(token_a)
    if not diagram_id:
        print("❌ Failed to create diagram")
        return False
    print(f"✅ Diagram created with ID: {diagram_id}, version: {initial_version}")
    print()

    # Step 3: User A shares diagram with User B (edit permission)
    print("Step 3: User A shares diagram with User B (edit permission)...")

    # Share diagram with User B using email
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    share_data = {
        "permission": "edit",
        "shared_with_email": user_b_email
    }
    response = requests.post(
        f"{DIAGRAM_API}/{diagram_id}/share",
        json=share_data,
        headers=headers_a
    )
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to share diagram (status {response.status_code}): {response.text}")
        return False
    print(f"✅ Diagram shared with User B (edit permission)")
    print()

    # Step 4: User A fetches diagram
    print("Step 4: User A fetches diagram...")
    response = requests.get(f"{DIAGRAM_API}/{diagram_id}", headers=headers_a)
    if response.status_code != 200:
        print(f"❌ Failed to fetch diagram: {response.text}")
        return False

    data_a = response.json()
    version_a = data_a.get("current_version")
    print(f"✅ User A fetched diagram, current version: {version_a}")
    print()

    # Step 5: User B fetches diagram (same version)
    print("Step 5: User B fetches diagram...")
    response = requests.get(f"{DIAGRAM_API}/{diagram_id}", headers=headers_b)
    if response.status_code != 200:
        print(f"❌ Failed to fetch diagram: {response.text}")
        return False

    data_b = response.json()
    version_b = data_b.get("current_version")
    print(f"✅ User B fetched diagram, current version: {version_b}")

    if version_b != version_a:
        print(f"❌ User B's version ({version_b}) doesn't match User A's version ({version_a})")
        return False
    print()

    # Step 6: User A updates diagram
    print(f"Step 6: User A updates diagram with expected_version={version_a}...")
    update_data_a = {
        "canvas_data": {
            "shapes": [
                {"id": "shape_a", "type": "rectangle", "x": 100, "y": 100}
            ]
        },
        "expected_version": version_a
    }
    response = requests.put(
        f"{DIAGRAM_API}/{diagram_id}",
        json=update_data_a,
        headers=headers_a
    )
    if response.status_code != 200:
        print(f"❌ User A's update failed: {response.text}")
        return False

    data = response.json()
    new_version_a = data.get("current_version")
    print(f"✅ User A's update succeeded, new version: {new_version_a}")

    if new_version_a <= version_a:
        print(f"❌ Version didn't increment (was {version_a}, now {new_version_a})")
        return False
    print()

    # Step 7: User B attempts to update with old version (should fail)
    print(f"Step 7: User B attempts to update with expected_version={version_b} (should fail)...")
    update_data_b = {
        "canvas_data": {
            "shapes": [
                {"id": "shape_b", "type": "circle", "x": 200, "y": 200}
            ]
        },
        "expected_version": version_b  # Still version 5
    }
    response = requests.put(
        f"{DIAGRAM_API}/{diagram_id}",
        json=update_data_b,
        headers=headers_b
    )

    # Should get 409 Conflict
    if response.status_code != 409:
        print(f"❌ Expected 409 Conflict, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    print(f"✅ User B's update rejected with 409 Conflict")

    # Step 8: Verify error message
    print("Step 8: Verify error message contains 'Diagram was modified by another user'...")
    error_detail = response.json().get("detail", "")

    if "Diagram was modified by another user" not in error_detail:
        print(f"❌ Error message doesn't contain expected text")
        print(f"Got: {error_detail}")
        return False

    print(f"✅ Error message verified: {error_detail}")
    print()

    # Step 9: User B refetches diagram (should see new version)
    print("Step 9: User B refetches diagram...")
    response = requests.get(f"{DIAGRAM_API}/{diagram_id}", headers=headers_b)
    if response.status_code != 200:
        print(f"❌ Failed to refetch diagram: {response.text}")
        return False

    data_b_new = response.json()
    version_b_new = data_b_new.get("current_version")
    print(f"✅ User B refetched diagram, current version: {version_b_new}")

    if version_b_new != new_version_a:
        print(f"❌ Expected version {new_version_a}, got {version_b_new}")
        return False
    print()

    # Step 10: User B updates successfully with new version
    print(f"Step 10: User B updates successfully with expected_version={version_b_new}...")
    update_data_b_retry = {
        "canvas_data": {
            "shapes": [
                {"id": "shape_b", "type": "circle", "x": 200, "y": 200}
            ]
        },
        "expected_version": version_b_new
    }
    response = requests.put(
        f"{DIAGRAM_API}/{diagram_id}",
        json=update_data_b_retry,
        headers=headers_b
    )

    if response.status_code != 200:
        print(f"❌ User B's retry update failed: {response.text}")
        return False

    data = response.json()
    final_version = data.get("current_version")
    print(f"✅ User B's update succeeded")
    print(f"   Current version: {final_version}")
    print(f"   Note: Version number stays same if <5min since last version or not a major edit")
    print()

    # All tests passed
    print("=" * 80)
    print("✅ ALL TESTS PASSED - Feature #127: Optimistic Locking")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"1. ✅ User A fetched diagram (version {version_a})")
    print(f"2. ✅ User B fetched diagram (version {version_b})")
    print(f"3. ✅ User A updated diagram (version {new_version_a})")
    print("4. ✅ User B's update with old version rejected (409 Conflict)")
    print("5. ✅ Error message: 'Diagram was modified by another user'")
    print(f"6. ✅ User B refetched diagram (version {version_b_new})")
    print(f"7. ✅ User B updated successfully (version {final_version})")
    print()
    print("Optimistic locking prevents concurrent edit conflicts!")
    print()

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
