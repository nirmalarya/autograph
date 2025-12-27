#!/usr/bin/env python3
"""
Feature #580 Validation: Organization: Folders: rename folder

Tests folder renaming functionality.

Steps:
1. Create a test user and login
2. Create a folder with initial name
3. Rename the folder via PUT /api/folders/{folder_id}
4. Verify the folder was renamed
5. Get folder to confirm name persists
"""

import requests
import json
import sys
from datetime import datetime
import bcrypt
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8080"

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def test_feature_580_rename_folder():
    """Test Feature #580: Rename folder."""

    print("=" * 80)
    print("Feature #580: Organization: Folders: rename folder")
    print("=" * 80)

    # Step 1: Create test user
    print("\n[Step 1] Creating test user...")
    test_user_email = f"folder_rename_test_{datetime.now().timestamp()}@example.com"
    test_user_password = "TestPassword123!"

    register_data = {
        "email": test_user_email,
        "password": test_user_password,
        "full_name": "Folder Rename Test User"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data, verify=False)
    if response.status_code != 201:
        print(f"❌ Failed to register user: {response.status_code} - {response.text}")
        return False

    print(f"✅ User registered: {test_user_email}")

    # Step 2: Login
    print("\n[Step 2] Logging in...")
    login_data = {
        "email": test_user_email,
        "password": test_user_password
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, verify=False)
    if response.status_code != 200:
        print(f"❌ Failed to login: {response.status_code} - {response.text}")
        return False

    token = response.json()["access_token"]
    user_id = response.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    print(f"✅ Logged in successfully")

    # Step 3: Create a folder with initial name
    print("\n[Step 3] Creating folder with initial name...")
    initial_folder_name = "Initial Folder Name"
    folder_data = {
        "name": initial_folder_name
    }

    response = requests.post(
        f"{BASE_URL}/api/diagrams/folders",
        json=folder_data,
        headers=headers,
        verify=False
    )

    if response.status_code != 201:
        print(f"❌ Failed to create folder: {response.status_code} - {response.text}")
        return False

    folder = response.json()
    folder_id = folder["id"]

    print(f"✅ Folder created with name: '{initial_folder_name}'")
    print(f"   Folder ID: {folder_id}")

    # Step 4: Rename the folder
    print("\n[Step 4] Renaming folder...")
    new_folder_name = "Renamed Folder Name"
    rename_data = {
        "name": new_folder_name
    }

    response = requests.put(
        f"{BASE_URL}/api/diagrams/folders/{folder_id}",
        json=rename_data,
        headers=headers,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to rename folder: {response.status_code} - {response.text}")
        return False

    updated_folder = response.json()

    if updated_folder["name"] != new_folder_name:
        print(f"❌ Folder name mismatch!")
        print(f"   Expected: '{new_folder_name}'")
        print(f"   Got: '{updated_folder['name']}'")
        return False

    print(f"✅ Folder renamed successfully")
    print(f"   Old name: '{initial_folder_name}'")
    print(f"   New name: '{new_folder_name}'")

    # Step 5: Get folder to confirm name persists
    print("\n[Step 5] Verifying renamed folder persists...")
    response = requests.get(
        f"{BASE_URL}/api/diagrams/folders/{folder_id}",
        headers=headers,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to get folder: {response.status_code} - {response.text}")
        return False

    folder = response.json()

    if folder["name"] != new_folder_name:
        print(f"❌ Folder name not persisted!")
        print(f"   Expected: '{new_folder_name}'")
        print(f"   Got: '{folder['name']}'")
        return False

    print(f"✅ Folder name persisted correctly: '{folder['name']}'")

    # Step 6: Test edge cases
    print("\n[Step 6] Testing edge cases...")

    # Test empty name (should fail)
    print("   Testing empty name...")
    response = requests.put(
        f"{BASE_URL}/api/diagrams/folders/{folder_id}",
        json={"name": ""},
        headers=headers,
        verify=False
    )

    if response.status_code == 200:
        # Check if database constraint prevents this
        folder_check = requests.get(
            f"{BASE_URL}/api/diagrams/folders/{folder_id}",
            headers=headers,
            verify=False
        ).json()

        if folder_check["name"] == "":
            print(f"   ⚠️  Warning: Empty folder name allowed")
        else:
            print(f"   ✅ Empty name rejected (folder unchanged)")
    else:
        print(f"   ✅ Empty name rejected with status {response.status_code}")

    # Test very long name
    print("   Testing very long name...")
    long_name = "A" * 300
    response = requests.put(
        f"{BASE_URL}/api/diagrams/folders/{folder_id}",
        json={"name": long_name},
        headers=headers,
        verify=False
    )

    if response.status_code == 200:
        # Check actual stored name
        folder_check = requests.get(
            f"{BASE_URL}/api/diagrams/folders/{folder_id}",
            headers=headers,
            verify=False
        ).json()

        if len(folder_check["name"]) > 255:
            print(f"   ⚠️  Warning: Very long names allowed ({len(folder_check['name'])} chars)")
        else:
            print(f"   ✅ Long name handled (truncated or accepted)")
    else:
        print(f"   ✅ Long name validation working")

    # Cleanup: Delete folder
    print("\n[Cleanup] Deleting test folder...")
    response = requests.delete(
        f"{BASE_URL}/api/diagrams/folders/{folder_id}",
        headers=headers,
        verify=False
    )

    if response.status_code in [200, 204]:
        print("✅ Test folder deleted")
    else:
        print(f"⚠️  Warning: Could not delete folder: {response.status_code}")

    print("\n" + "=" * 80)
    print("✅ Feature #580 PASSED: Folder rename works correctly!")
    print("=" * 80)

    return True

if __name__ == "__main__":
    try:
        success = test_feature_580_rename_folder()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
