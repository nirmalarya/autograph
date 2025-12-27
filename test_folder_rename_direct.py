#!/usr/bin/env python3
"""Direct test of folder rename via diagram service"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8082"
user_id = "folder-rename-test-user-580"
headers = {"X-User-ID": user_id}

# Create folder
print("Creating folder...")
response = requests.post(
    f"{BASE_URL}/folders",
    json={"name": "Initial Folder Name"},
    headers=headers,
    verify=False
)

print(f"Status: {response.status_code}")
if response.status_code != 201:
    print(f"Error: {response.text}")
    exit(1)

folder = response.json()
folder_id = folder["id"]
print(f"✅ Created: {folder['name']} (ID: {folder_id})")

# Rename folder
print("\nRenaming folder...")
response = requests.put(
    f"{BASE_URL}/folders/{folder_id}",
    json={"name": "Renamed Folder Name"},
    headers=headers,
    verify=False
)

print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
    exit(1)

folder = response.json()
print(f"✅ Renamed to: {folder['name']}")

# Verify
print("\nVerifying...")
response = requests.get(
    f"{BASE_URL}/folders/{folder_id}",
    headers=headers,
    verify=False
)

if response.status_code != 200:
    print(f"Error: {response.text}")
    exit(1)

folder = response.json()
if folder["name"] != "Renamed Folder Name":
    print(f"❌ Failed: {folder['name']}")
    exit(1)

print(f"✅ Verified: {folder['name']}")

# Cleanup
requests.delete(f"{BASE_URL}/folders/{folder_id}", headers=headers, verify=False)

print("\n✅ Feature #580 PASSED: Folder rename works!")
