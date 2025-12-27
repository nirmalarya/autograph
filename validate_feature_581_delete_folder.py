#!/usr/bin/env python3
"""
Feature #581: Organization: Folders: delete folder
Tests that deleting a folder moves all contents to trash
"""

import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Test user credentials
TEST_USER_ID = "581-test-user-id"
TEST_EMAIL = "feature581@test.com"
TEST_PASSWORD = "password"

print("=" * 70)
print("Feature #581: Delete folder with contents moved to trash")
print("=" * 70)

# Step 1: Login to get JWT token
print("\n1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    verify=False
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}
print(f"✅ Login successful, got token")

# Step 2: Create a folder
print("\n2. Creating test folder...")
folder_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/folders",
    headers=headers,
    json={"name": "Test Folder to Delete"},
    verify=False
)

if folder_response.status_code != 200:
    print(f"❌ Failed to create folder: {folder_response.status_code}")
    print(f"Response: {folder_response.text}")
    exit(1)

folder = folder_response.json()
folder_id = folder["id"]
print(f"✅ Created folder: {folder_id}")

# Step 3: Create multiple files in the folder
print("\n3. Creating files in folder...")
file_ids = []

for i in range(3):
    file_data = {
        "name": f"Test File {i+1}",
        "file_type": "diagram",
        "content": f'{{"type": "test", "data": "file {i+1}"}}',
        "folder_id": folder_id
    }

    file_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/files",
        headers=headers,
        json=file_data,
        verify=False
    )

    if file_response.status_code != 200:
        print(f"❌ Failed to create file {i+1}: {file_response.status_code}")
        print(f"Response: {file_response.text}")
        exit(1)

    file = file_response.json()
    file_ids.append(file["id"])
    print(f"   ✅ Created file {i+1}: {file['id']}")

print(f"✅ Created {len(file_ids)} files in folder")

# Step 4: Verify files are not in trash before deletion
print("\n4. Verifying files are active (not in trash)...")
for file_id in file_ids:
    file_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/files/{file_id}",
        headers=headers,
        verify=False
    )

    if file_response.status_code != 200:
        print(f"❌ Failed to get file {file_id}")
        exit(1)

    file = file_response.json()
    if file.get("is_deleted"):
        print(f"❌ File {file_id} is already deleted!")
        exit(1)

print(f"✅ All {len(file_ids)} files are active")

# Step 5: Delete the folder
print(f"\n5. Deleting folder {folder_id}...")
delete_response = requests.delete(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if delete_response.status_code != 200:
    print(f"❌ Failed to delete folder: {delete_response.status_code}")
    print(f"Response: {delete_response.text}")
    exit(1)

delete_result = delete_response.json()
print(f"✅ Folder deleted successfully")
print(f"   Files moved to trash: {delete_result.get('files_moved_to_trash', 0)}")

# Step 6: Verify folder is deleted
print("\n6. Verifying folder is deleted...")
folder_check = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if folder_check.status_code != 404:
    print(f"❌ Folder still exists! Status: {folder_check.status_code}")
    exit(1)

print(f"✅ Folder no longer exists")

# Step 7: Verify all files are in trash (soft-deleted)
print("\n7. Verifying files are in trash...")
trashed_count = 0

for file_id in file_ids:
    file_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/files/{file_id}",
        headers=headers,
        verify=False
    )

    if file_response.status_code != 200:
        print(f"⚠️  File {file_id} not accessible (might be soft-deleted)")
        continue

    file = file_response.json()
    if file.get("is_deleted"):
        trashed_count += 1
        print(f"   ✅ File {file_id} is in trash (is_deleted=True)")
    else:
        print(f"   ❌ File {file_id} is NOT in trash!")

if trashed_count != len(file_ids):
    print(f"❌ Expected {len(file_ids)} files in trash, found {trashed_count}")
    exit(1)

print(f"✅ All {len(file_ids)} files moved to trash")

# Step 8: Verify files in trash endpoint
print("\n8. Verifying files appear in trash list...")
trash_response = requests.get(
    f"{DIAGRAM_SERVICE_URL}/files/trash",
    headers=headers,
    verify=False
)

if trash_response.status_code != 200:
    print(f"⚠️  Could not retrieve trash: {trash_response.status_code}")
else:
    trash_files = trash_response.json()
    trash_file_ids = [f["id"] for f in trash_files]

    found_in_trash = sum(1 for fid in file_ids if fid in trash_file_ids)
    print(f"   Found {found_in_trash}/{len(file_ids)} files in trash endpoint")

    if found_in_trash == len(file_ids):
        print(f"✅ All files appear in trash list")

print("\n" + "=" * 70)
print("✅ Feature #581 PASSED: Delete folder with contents to trash!")
print("=" * 70)
print("\nSummary:")
print(f"- Created folder with {len(file_ids)} files")
print(f"- Deleted folder successfully")
print(f"- All {len(file_ids)} files moved to trash (soft-deleted)")
print(f"- Folder no longer exists")
