#!/usr/bin/env python3
"""
Feature #582: Organization: Folders: colors and icons
Test that folders can be customized with colors and icons.

Steps:
1. Create a folder
2. Update folder with color (blue: #0000FF)
3. Verify folder is blue
4. Update folder with icon (folder-star)
5. Verify icon is updated
"""

import requests
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration - Direct to diagram service
DIAGRAM_SERVICE_URL = "https://localhost:8082"

# Test user
TEST_USER_ID = "582-test-user-colors-icons"

headers = {
    "X-User-ID": TEST_USER_ID,
    "Content-Type": "application/json"
}

print("=" * 80)
print("Feature #582: Organization: Folders: colors and icons")
print("=" * 80)

# Step 1: Create a folder
print("\n1. Creating test folder...")
folder_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/folders",
    headers=headers,
    json={"name": "Color Test Folder"},
    verify=False
)

if folder_response.status_code not in [200, 201]:
    print(f"❌ Failed to create folder: {folder_response.status_code}")
    print(f"Response: {folder_response.text}")
    sys.exit(1)

folder = folder_response.json()
folder_id = folder["id"]
print(f"✅ Created folder: {folder_id}")
print(f"   Name: {folder['name']}")
print(f"   Initial color: {folder.get('color', 'None')}")
print(f"   Initial icon: {folder.get('icon', 'None')}")

# Step 2: Update folder with blue color (#0000FF)
print("\n2. Updating folder color to blue (#0000FF)...")
update_response = requests.put(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    json={"color": "#0000FF"},
    verify=False
)

if update_response.status_code != 200:
    print(f"❌ Failed to update folder color: {update_response.status_code}")
    print(f"Response: {update_response.text}")
    sys.exit(1)

updated_folder = update_response.json()
print(f"✅ Folder color updated")
print(f"   Color: {updated_folder.get('color')}")

# Step 3: Verify folder is blue
print("\n3. Verifying folder color via GET...")
get_response = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if get_response.status_code != 200:
    print(f"❌ Failed to get folder: {get_response.status_code}")
    sys.exit(1)

folder_data = get_response.json()
if folder_data.get('color') != '#0000FF':
    print(f"❌ Color mismatch! Expected: #0000FF, Got: {folder_data.get('color')}")
    sys.exit(1)

print(f"✅ Folder is blue: {folder_data.get('color')}")

# Step 4: Update folder with icon (folder-star)
print("\n4. Updating folder icon to 'folder-star'...")
update_response = requests.put(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    json={"icon": "folder-star"},
    verify=False
)

if update_response.status_code != 200:
    print(f"❌ Failed to update folder icon: {update_response.status_code}")
    print(f"Response: {update_response.text}")
    sys.exit(1)

updated_folder = update_response.json()
print(f"✅ Folder icon updated")
print(f"   Icon: {updated_folder.get('icon')}")

# Step 5: Verify icon is updated
print("\n5. Verifying folder icon via GET...")
get_response = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if get_response.status_code != 200:
    print(f"❌ Failed to get folder: {get_response.status_code}")
    sys.exit(1)

folder_data = get_response.json()
if folder_data.get('icon') != 'folder-star':
    print(f"❌ Icon mismatch! Expected: folder-star, Got: {folder_data.get('icon')}")
    sys.exit(1)

print(f"✅ Folder icon is 'folder-star': {folder_data.get('icon')}")

# Step 6: Update both color and icon together
print("\n6. Updating both color and icon together...")
update_response = requests.put(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    json={"color": "#FF0000", "icon": "folder-heart"},
    verify=False
)

if update_response.status_code != 200:
    print(f"❌ Failed to update folder: {update_response.status_code}")
    print(f"Response: {update_response.text}")
    sys.exit(1)

updated_folder = update_response.json()
if updated_folder.get('color') != '#FF0000' or updated_folder.get('icon') != 'folder-heart':
    print(f"❌ Simultaneous update failed!")
    print(f"   Expected: color=#FF0000, icon=folder-heart")
    print(f"   Got: color={updated_folder.get('color')}, icon={updated_folder.get('icon')}")
    sys.exit(1)

print(f"✅ Both color and icon updated successfully")
print(f"   Color: {updated_folder.get('color')}")
print(f"   Icon: {updated_folder.get('icon')}")

# Step 7: Verify via GET again
print("\n7. Final verification via GET...")
get_response = requests.get(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

folder_data = get_response.json()
if folder_data.get('color') != '#FF0000':
    print(f"❌ Final color wrong: {folder_data.get('color')}")
    sys.exit(1)
if folder_data.get('icon') != 'folder-heart':
    print(f"❌ Final icon wrong: {folder_data.get('icon')}")
    sys.exit(1)

print(f"✅ Final verification passed")
print(f"   Color: {folder_data.get('color')}")
print(f"   Icon: {folder_data.get('icon')}")

# Cleanup
print("\n8. Cleaning up test folder...")
delete_response = requests.delete(
    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if delete_response.status_code == 200:
    print(f"✅ Test folder deleted")
else:
    print(f"⚠️  Could not delete test folder (status {delete_response.status_code})")

print("\n" + "=" * 80)
print("✅✅✅ Feature #582 PASSED: Folder colors and icons!")
print("=" * 80)
print("\nSummary:")
print(f"- Created folder successfully")
print(f"- Updated folder color to blue (#0000FF) ✅")
print(f"- Updated folder icon to 'folder-star' ✅")
print(f"- Updated both color and icon together ✅")
print(f"- All updates persisted correctly ✅")
print("\nFeature works correctly! ✅")
