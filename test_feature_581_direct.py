#!/usr/bin/env python3
"""
Feature #581: Organization: Folders: delete folder (DIRECT TEST)
Tests that deleting a folder moves all contents to trash
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration - Direct to diagram service
DIAGRAM_SERVICE_URL = "https://localhost:8082"

# Test user
TEST_USER_ID = "581-test-user-id"

headers = {
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}

print("=" * 70)
print("Feature #581: Delete folder with contents (DIRECT TEST)")
print("=" * 70)

# Step 1: Create a folder
print("\n1. Creating test folder...")
folder_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/folders",
    headers=headers,
    json={"name": "Test Folder to Delete"},
    verify=False
)

if folder_response.status_code not in [200, 201]:
    print(f"❌ Failed to create folder: {folder_response.status_code}")
    print(f"Response: {folder_response.text}")
    exit(1)

folder = folder_response.json()
folder_id = folder["id"]
print(f"✅ Created folder: {folder_id}")

# Step 2: Create multiple files in the folder
print("\n2. Creating files in folder...")
file_ids = []

for i in range(3):
    file_data = {
        "title": f"Test File {i+1}",
        "file_type": "canvas",
        "canvas_data": {"type": "test", "data": f"file {i+1}"},
        "folder_id": folder_id
    }

    file_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json=file_data,
        verify=False
    )

    if file_response.status_code not in [200, 201]:
        print(f"❌ Failed to create file {i+1}: {file_response.status_code}")
        print(f"Response: {file_response.text}")
        exit(1)

    file = file_response.json()
    file_ids.append(file["id"])
    print(f"   ✅ Created file {i+1}: {file['id']}")

print(f"✅ Created {len(file_ids)} files in folder")

# Step 3: Delete the folder
print(f"\n3. Deleting folder {folder_id}...")
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

# Step 4: Verify folder is deleted
print("\n4. Verifying folder is deleted...")
folder_check = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if folder_check.status_code != 404:
    print(f"❌ Folder still exists! Status: {folder_check.status_code}")
    exit(1)

print(f"✅ Folder no longer exists")

# Step 5: Verify all files are in trash (soft-deleted)
print("\n5. Verifying files are in trash...")
trashed_count = 0

for file_id in file_ids:
    file_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{file_id}",
        headers=headers,
        verify=False
    )

    if file_response.status_code != 200:
        print(f"⚠️  File {file_id} not accessible")
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

print("\n" + "=" * 70)
print("✅ Feature #581 PASSED: Delete folder with contents to trash!")
print("=" * 70)
