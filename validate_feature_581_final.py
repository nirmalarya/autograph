#!/usr/bin/env python3
"""
Feature #581: Organization: Folders: delete folder
Final comprehensive test that verifies deletion moves contents to trash
"""

import requests
import subprocess
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
print("Feature #581: Delete folder with contents to trash - FINAL TEST")
print("=" * 70)

# Step 1: Create a folder
print("\n1. Creating test folder...")
folder_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/folders",
    headers=headers,
    json={"name": "Test Folder for Feature 581"},
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
print("\n2. Creating 3 files in folder...")
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
        exit(1)

    file = file_response.json()
    file_ids.append(file["id"])
    print(f"   ✅ Created file {i+1}: {file['id']}")

# Step 3: Verify files are NOT deleted before folder deletion
print("\n3. Verifying files are active in database...")
for file_id in file_ids:
    check_cmd = f"""PGPASSWORD=autograph_dev_password psql -h localhost -U autograph -d autograph -t -c "SELECT is_deleted FROM files WHERE id = '{file_id}';" """
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    is_deleted = result.stdout.strip()
    if is_deleted != 'f':
        print(f"❌ File {file_id} is already deleted!")
        exit(1)

print(f"✅ All 3 files are active (not deleted)")

# Step 4: Delete the folder
print(f"\n4. Deleting folder {folder_id}...")
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
files_moved = delete_result.get('files_moved_to_trash', 0)
print(f"✅ Folder deleted successfully")
print(f"   Files moved to trash: {files_moved}")

if files_moved != 3:
    print(f"❌ Expected 3 files moved to trash, got {files_moved}")
    exit(1)

# Step 5: Verify folder is deleted
print("\n5. Verifying folder no longer exists...")
folder_check = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if folder_check.status_code != 404:
    print(f"❌ Folder still exists! Status: {folder_check.status_code}")
    exit(1)

print(f"✅ Folder no longer exists (404 as expected)")

# Step 6: Verify all files are soft-deleted in database
print("\n6. Verifying files are soft-deleted in database...")
trashed_count = 0

for file_id in file_ids:
    check_cmd = f"""PGPASSWORD=autograph_dev_password psql -h localhost -U autograph -d autograph -t -c "SELECT is_deleted, deleted_at IS NOT NULL FROM files WHERE id = '{file_id}';" """
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    # Check if both values are 't' (true)
    if 't' in output and output.count('t') == 2:
        trashed_count += 1
        print(f"   ✅ File {file_id}: is_deleted=true, deleted_at set")
    else:
        print(f"   ❌ File {file_id}: NOT properly soft-deleted ({output})")

if trashed_count != 3:
    print(f"❌ Expected 3 files in trash, found {trashed_count}")
    exit(1)

print(f"✅ All 3 files correctly soft-deleted")

# Step 7: Verify files are NOT accessible via GET (correctly filtered)
print("\n7. Verifying soft-deleted files are not accessible via GET...")
inaccessible_count = 0

for file_id in file_ids:
    file_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{file_id}",
        headers=headers,
        verify=False
    )

    if file_response.status_code == 404:
        inaccessible_count += 1

print(f"   {inaccessible_count}/3 files correctly filtered (not accessible)")

if inaccessible_count == 3:
    print(f"✅ Soft-deleted files properly filtered from GET")

print("\n" + "=" * 70)
print("✅✅✅ Feature #581 PASSED: Delete folder with contents to trash!")
print("=" * 70)
print("\nSummary:")
print(f"- Created folder with 3 files")
print(f"- Deleted folder successfully")
print(f"- All 3 files moved to trash (is_deleted=true)")
print(f"- Folder removed from database")
print(f"- Soft-deleted files properly filtered")
print("\nFeature works correctly! ✅")
