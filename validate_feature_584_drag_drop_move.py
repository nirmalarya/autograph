#!/usr/bin/env python3
"""
Feature #584: Organization: Drag-drop: move files to folders
Tests the ability to move diagrams to folders using drag-drop (backend move operation)
"""

import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
BASE_URL = "https://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Test user credentials
TEST_USER_ID = "584-test-user-id"
TEST_EMAIL = "feature584@test.com"
TEST_PASSWORD = "SecurePass123!"

print("=" * 70)
print("Feature #584: Drag-drop move files to folders")
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
    json={"name": "Drag Drop Target Folder"},
    verify=False
)

if folder_response.status_code != 200:
    print(f"❌ Failed to create folder: {folder_response.status_code}")
    print(f"Response: {folder_response.text}")
    exit(1)

folder = folder_response.json()
folder_id = folder["id"]
print(f"✅ Created folder: {folder_id} - '{folder['name']}'")

# Step 3: Create a diagram (not in any folder initially)
print("\n3. Creating diagram in root (no folder)...")
diagram_data = {
    "name": "Diagram to Move",
    "file_type": "diagram",
    "content": '{"type": "flowchart", "elements": [{"id": "1", "type": "rectangle", "text": "Start"}]}'
}

diagram_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/files",
    headers=headers,
    json=diagram_data,
    verify=False
)

if diagram_response.status_code != 200:
    print(f"❌ Failed to create diagram: {diagram_response.status_code}")
    print(f"Response: {diagram_response.text}")
    exit(1)

diagram = diagram_response.json()
diagram_id = diagram["id"]
print(f"✅ Created diagram: {diagram_id} - '{diagram['name']}'")
print(f"   Initial folder_id: {diagram.get('folder_id', 'None (root)')}")

# Step 4: Verify diagram is in root (no folder_id)
if diagram.get("folder_id"):
    print(f"❌ Diagram should be in root but has folder_id: {diagram.get('folder_id')}")
    exit(1)
print(f"✅ Diagram is in root (no folder)")

# Step 5: Move diagram to folder (simulating drag-drop)
print(f"\n4. Moving diagram to folder (drag-drop)...")
move_response = requests.put(
    f"{DIAGRAM_SERVICE_URL}/{diagram_id}/move",
    headers=headers,
    json={"folder_id": folder_id},
    verify=False
)

if move_response.status_code != 200:
    print(f"❌ Failed to move diagram: {move_response.status_code}")
    print(f"Response: {move_response.text}")
    exit(1)

move_result = move_response.json()
print(f"✅ Diagram moved successfully")
print(f"   Message: {move_result.get('message')}")
print(f"   New folder_id: {move_result.get('folder_id')}")

# Step 6: Verify diagram is now in the folder
print("\n5. Verifying diagram moved to folder...")
diagram_check = requests.get(
    f"{DIAGRAM_SERVICE_URL}/files/{diagram_id}",
    headers=headers,
    verify=False
)

if diagram_check.status_code != 200:
    print(f"❌ Failed to get diagram: {diagram_check.status_code}")
    exit(1)

updated_diagram = diagram_check.json()
if updated_diagram.get("folder_id") != folder_id:
    print(f"❌ Diagram folder_id mismatch!")
    print(f"   Expected: {folder_id}")
    print(f"   Got: {updated_diagram.get('folder_id')}")
    exit(1)

print(f"✅ Diagram is now in folder {folder_id}")

# Step 7: Verify diagram appears in folder listing
print("\n6. Verifying diagram appears in folder listing...")
folder_files_response = requests.get(
    f"{DIAGRAM_SERVICE_URL}/files?folder_id={folder_id}",
    headers=headers,
    verify=False
)

if folder_files_response.status_code != 200:
    print(f"❌ Failed to get folder files: {folder_files_response.status_code}")
    exit(1)

folder_files = folder_files_response.json()
file_ids_in_folder = [f["id"] for f in folder_files]

if diagram_id not in file_ids_in_folder:
    print(f"❌ Diagram {diagram_id} not found in folder listing!")
    print(f"   Files in folder: {file_ids_in_folder}")
    exit(1)

print(f"✅ Diagram appears in folder listing")
print(f"   Folder contains {len(folder_files)} file(s)")

# Step 8: Test moving diagram back to root
print("\n7. Testing move back to root (no folder)...")
move_to_root = requests.put(
    f"{DIAGRAM_SERVICE_URL}/{diagram_id}/move",
    headers=headers,
    json={"folder_id": None},
    verify=False
)

if move_to_root.status_code != 200:
    print(f"❌ Failed to move to root: {move_to_root.status_code}")
    print(f"Response: {move_to_root.text}")
    exit(1)

print(f"✅ Moved diagram back to root")

# Step 9: Verify diagram is back in root
diagram_check2 = requests.get(
    f"{DIAGRAM_SERVICE_URL}/files/{diagram_id}",
    headers=headers,
    verify=False
)

if diagram_check2.status_code != 200:
    print(f"❌ Failed to get diagram: {diagram_check2.status_code}")
    exit(1)

root_diagram = diagram_check2.json()
if root_diagram.get("folder_id") is not None:
    print(f"❌ Diagram should be in root but has folder_id: {root_diagram.get('folder_id')}")
    exit(1)

print(f"✅ Diagram is back in root (folder_id is None)")

# Step 10: Test moving to another folder
print("\n8. Creating second folder and moving diagram...")
folder2_response = requests.post(
    f"{DIAGRAM_SERVICE_URL}/folders",
    headers=headers,
    json={"name": "Second Target Folder"},
    verify=False
)

if folder2_response.status_code != 200:
    print(f"❌ Failed to create second folder: {folder2_response.status_code}")
    exit(1)

folder2 = folder2_response.json()
folder2_id = folder2["id"]
print(f"✅ Created second folder: {folder2_id}")

move_response2 = requests.put(
    f"{DIAGRAM_SERVICE_URL}/{diagram_id}/move",
    headers=headers,
    json={"folder_id": folder2_id},
    verify=False
)

if move_response2.status_code != 200:
    print(f"❌ Failed to move to second folder: {move_response2.status_code}")
    exit(1)

print(f"✅ Moved diagram to second folder")

# Final verification
diagram_check3 = requests.get(
    f"{DIAGRAM_SERVICE_URL}/files/{diagram_id}",
    headers=headers,
    verify=False
)

final_diagram = diagram_check3.json()
if final_diagram.get("folder_id") != folder2_id:
    print(f"❌ Diagram should be in folder2 but has folder_id: {final_diagram.get('folder_id')}")
    exit(1)

print(f"✅ Diagram is now in second folder")

print("\n" + "=" * 70)
print("✅ Feature #584 PASSED: Drag-drop move files to folders!")
print("=" * 70)
print("\nSummary:")
print(f"- Created 2 folders and 1 diagram")
print(f"- Successfully moved diagram from root to folder 1")
print(f"- Successfully moved diagram from folder 1 back to root")
print(f"- Successfully moved diagram from root to folder 2")
print(f"- Diagram correctly appears in folder listings")
print(f"- All move operations validated ✅")
