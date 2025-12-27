#!/usr/bin/env python3
"""
Feature 582: Organization: Folders: colors and icons
Test that folders can be customized with colors and icons.

Steps:
1. Create a folder
2. Update folder with color (blue: #0000FF)
3. Verify folder is blue
4. Update folder with icon (folder-star)
5. Verify icon is updated
"""

import requests
import sys
import json
from datetime import datetime

API_BASE = "https://localhost:8080"
DIAGRAM_SERVICE = "https://localhost:8082"

# Disable SSL warnings for local testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_test_user():
    """Create a test user for this feature."""
    import subprocess
    import bcrypt

    # Generate password hash
    password = "TestPass123!"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create user in database
    sql = f"""
    INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
    VALUES (
        'test-user-582-folder-colors',
        'folder-colors-test@example.com',
        '{password_hash}',
        'Folder Colors Test User',
        true,
        true,
        'user',
        NOW(),
        NOW()
    )
    ON CONFLICT (email) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        updated_at = NOW();
    """

    result = subprocess.run(
        ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", sql],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to create user: {result.stderr}")
        return None

    return "test-user-582-folder-colors"

def login(email, password):
    """Login and get session token."""
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        verify=False  # Disable SSL verification for local testing
    )
    print(f"Login response: {response.status_code}")
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
    if response.status_code == 200:
        data = response.json()
        return data.get("session_token")
    return None

def create_folder(session_token, user_id, name="Test Folder"):
    """Create a folder."""
    response = requests.post(
        f"{API_BASE}/folders",
        json={"name": name},
        headers={
            "Authorization": f"Bearer {session_token}",
            "X-User-ID": user_id
        },
        verify=False
    )
    return response

def update_folder(session_token, user_id, folder_id, color=None, icon=None):
    """Update a folder's color and/or icon."""
    data = {}
    if color is not None:
        data["color"] = color
    if icon is not None:
        data["icon"] = icon

    response = requests.put(
        f"{API_BASE}/folders/{folder_id}",
        json=data,
        headers={
            "Authorization": f"Bearer {session_token}",
            "X-User-ID": user_id
        },
        verify=False
    )
    return response

def get_folder(session_token, user_id, folder_id):
    """Get folder details."""
    response = requests.get(
        f"{API_BASE}/folders/{folder_id}",
        headers={
            "Authorization": f"Bearer {session_token}",
            "X-User-ID": user_id
        },
        verify=False
    )
    return response

def cleanup_folder(session_token, user_id, folder_id):
    """Delete a test folder."""
    try:
        response = requests.delete(
            f"{API_BASE}/folders/{folder_id}",
            headers={
                "Authorization": f"Bearer {session_token}",
                "X-User-ID": user_id
            },
            verify=False
        )
        print(f"Cleanup folder {folder_id}: {response.status_code}")
    except Exception as e:
        print(f"Failed to cleanup folder: {e}")

def main():
    print("=" * 80)
    print("Feature 582: Organization: Folders: colors and icons")
    print("=" * 80)

    # Create test user
    print("\n1. Creating test user...")
    user_id = create_test_user()
    if not user_id:
        print("❌ Failed to create test user")
        return False
    print(f"✅ Test user created: {user_id}")

    # Login
    print("\n2. Logging in...")
    session_token = login("folder-colors-test@example.com", "TestPass123!")
    if not session_token:
        print("❌ Failed to login")
        return False
    print(f"✅ Logged in successfully")

    folder_id = None

    try:
        # Step 1: Create a folder
        print("\n3. Creating a folder...")
        response = create_folder(session_token, user_id, "Color Test Folder")

        if response.status_code != 200:
            print(f"❌ Failed to create folder: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        folder_data = response.json()
        folder_id = folder_data["id"]
        print(f"✅ Folder created: {folder_id}")
        print(f"   Name: {folder_data['name']}")
        print(f"   Initial color: {folder_data.get('color', 'None')}")
        print(f"   Initial icon: {folder_data.get('icon', 'None')}")

        # Step 2: Update folder with blue color
        print("\n4. Updating folder color to blue (#0000FF)...")
        response = update_folder(session_token, user_id, folder_id, color="#0000FF")

        if response.status_code != 200:
            print(f"❌ Failed to update folder color: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        folder_data = response.json()
        print(f"✅ Folder color updated")
        print(f"   Color: {folder_data.get('color')}")

        # Step 3: Verify folder is blue
        print("\n5. Verifying folder color...")
        response = get_folder(session_token, user_id, folder_id)

        if response.status_code != 200:
            print(f"❌ Failed to get folder: {response.status_code}")
            return False

        folder_data = response.json()
        if folder_data.get('color') != '#0000FF':
            print(f"❌ Color mismatch! Expected: #0000FF, Got: {folder_data.get('color')}")
            return False

        print(f"✅ Folder is blue: {folder_data.get('color')}")

        # Step 4: Update folder with icon
        print("\n6. Updating folder icon to 'folder-star'...")
        response = update_folder(session_token, user_id, folder_id, icon="folder-star")

        if response.status_code != 200:
            print(f"❌ Failed to update folder icon: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        folder_data = response.json()
        print(f"✅ Folder icon updated")
        print(f"   Icon: {folder_data.get('icon')}")

        # Step 5: Verify icon is updated
        print("\n7. Verifying folder icon...")
        response = get_folder(session_token, user_id, folder_id)

        if response.status_code != 200:
            print(f"❌ Failed to get folder: {response.status_code}")
            return False

        folder_data = response.json()
        if folder_data.get('icon') != 'folder-star':
            print(f"❌ Icon mismatch! Expected: folder-star, Got: {folder_data.get('icon')}")
            return False

        print(f"✅ Folder icon is 'folder-star': {folder_data.get('icon')}")

        # Bonus: Update both at the same time
        print("\n8. Updating both color and icon together...")
        response = update_folder(session_token, user_id, folder_id, color="#FF0000", icon="folder-heart")

        if response.status_code != 200:
            print(f"❌ Failed to update folder: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        folder_data = response.json()
        if folder_data.get('color') != '#FF0000' or folder_data.get('icon') != 'folder-heart':
            print(f"❌ Simultaneous update failed!")
            print(f"   Expected: color=#FF0000, icon=folder-heart")
            print(f"   Got: color={folder_data.get('color')}, icon={folder_data.get('icon')}")
            return False

        print(f"✅ Both color and icon updated successfully")
        print(f"   Color: {folder_data.get('color')}")
        print(f"   Icon: {folder_data.get('icon')}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature 582 is working!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if folder_id:
            print("\n9. Cleaning up...")
            cleanup_folder(session_token, user_id, folder_id)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
