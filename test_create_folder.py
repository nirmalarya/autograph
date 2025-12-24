#!/usr/bin/env python3
"""
Test Feature #662: Create folder succeeds 100% of time

This script tests folder creation reliability:
1. Create a test user and login
2. Create 10 consecutive folders
3. Verify all 10 succeed without errors
4. Test with different folder properties (color, icon, parent)
"""

import requests
import json
import uuid
import psycopg2

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def setup_test_user():
    """Create and login a test user."""
    test_email = f"test-folder-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"

    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={"email": test_email, "password": test_password, "name": "Test Folder User"}
    )

    if register_response.status_code not in [200, 201]:
        raise Exception(f"Registration failed: {register_response.status_code}")

    user_id = register_response.json().get("id")

    # Verify email
    conn = psycopg2.connect(
        dbname="autograph", user="autograph", password="autograph_dev_password",
        host="localhost", port="5432"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": test_email, "password": test_password}
    )

    if login_response.status_code != 200:
        raise Exception(f"Login failed: {login_response.status_code}")

    access_token = login_response.json().get("access_token")
    return user_id, access_token, test_email

def test_create_folder():
    """Test folder creation reliability."""

    print("\n" + "="*80)
    print("TEST: Feature #662 - Create Folder Succeeds 100% of Time")
    print("="*80 + "\n")

    # Setup
    print("Setup: Creating test user...")
    user_id, access_token, email = setup_test_user()
    print(f"✅ Logged in as {email}\n")

    # Test 1: Create 10 consecutive folders
    print("Test 1: Creating 10 consecutive folders...")
    print("-" * 80)

    created_folders = []
    success_count = 0
    fail_count = 0

    for i in range(1, 11):
        folder_name = f"Test Folder {i}"

        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders",
            headers={"X-User-ID": user_id, "Content-Type": "application/json"},
            json={"name": folder_name}
        )

        if response.status_code == 201:
            folder = response.json()
            created_folders.append(folder)
            success_count += 1
            print(f"  ✅ Folder {i}: '{folder_name}' (ID: {folder['id'][:8]}...)")
        else:
            fail_count += 1
            print(f"  ❌ Folder {i}: Failed ({response.status_code})")
            print(f"     Response: {response.text[:100]}")

    print(f"\nResult: {success_count}/10 succeeded, {fail_count}/10 failed")

    if fail_count > 0:
        print(f"\n❌ TEST FAILED: {fail_count} folder creations failed!")
        return False

    print(f"✅ All 10 folders created successfully!")

    # Test 2: Create folder with properties
    print("\nTest 2: Creating folder with color and icon...")
    print("-" * 80)

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/folders",
        headers={"X-User-ID": user_id, "Content-Type": "application/json"},
        json={
            "name": "Colored Folder",
            "color": "#ff0000",
            "icon": "star"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create colored folder: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    colored_folder = response.json()
    print(f"✅ Created: '{colored_folder['name']}'")
    print(f"   Color: {colored_folder['color']}")
    print(f"   Icon: {colored_folder['icon']}")

    # Test 3: Create nested folder (with parent)
    print("\nTest 3: Creating nested folder (with parent)...")
    print("-" * 80)

    parent_id = created_folders[0]['id']

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/folders",
        headers={"X-User-ID": user_id, "Content-Type": "application/json"},
        json={
            "name": "Nested Folder",
            "parent_id": parent_id
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create nested folder: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    nested_folder = response.json()
    print(f"✅ Created: '{nested_folder['name']}'")
    print(f"   Parent ID: {nested_folder['parent_id'][:8]}...")

    # Test 4: Create 10 more folders rapidly (stress test)
    print("\nTest 4: Rapid creation stress test (10 more folders)...")
    print("-" * 80)

    rapid_success = 0
    rapid_fail = 0

    for i in range(11, 21):
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders",
            headers={"X-User-ID": user_id, "Content-Type": "application/json"},
            json={"name": f"Rapid Folder {i}"}
        )

        if response.status_code == 201:
            rapid_success += 1
        else:
            rapid_fail += 1
            print(f"  ❌ Folder {i} failed: {response.status_code}")

    print(f"Result: {rapid_success}/10 succeeded, {rapid_fail}/10 failed")

    if rapid_fail > 0:
        print(f"\n❌ Stress test failed: {rapid_fail} failures")
        return False

    print(f"✅ Stress test passed!")

    # Final summary
    total_created = success_count + 1 + 1 + rapid_success  # Basic 10 + colored + nested + rapid 10
    print("\n" + "="*80)
    print(f"✅ FEATURE #662 PASSING: Create folder succeeds 100% of time!")
    print(f"   Total folders created: {total_created}/22 (100% success rate)")
    print("="*80 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = test_create_folder()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
