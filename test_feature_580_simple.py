#!/usr/bin/env python3
"""Simple test for Feature #580: Rename folder"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8080"

# Login with pre-created test user
print("Logging in...")
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "folder_rename_580@example.com", "password": "TestPassword123!"},
    verify=False
)

if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Logged in")

# Create folder
print("\nCreating folder...")
response = requests.post(
    f"{BASE_URL}/api/diagrams/folders",
    json={"name": "Test Folder"},
    headers=headers,
    verify=False
)

if response.status_code != 201:
    print(f"Create failed: {response.status_code} - {response.text}")
    exit(1)

folder_id = response.json()["id"]
print(f"✅ Created folder: {folder_id}")

# Rename folder
print("\nRenaming folder...")
response = requests.put(
    f"{BASE_URL}/api/diagrams/folders/{folder_id}",
    json={"name": "Renamed Folder"},
    headers=headers,
    verify=False
)

if response.status_code != 200:
    print(f"Rename failed: {response.status_code} - {response.text}")
    exit(1)

folder = response.json()
if folder["name"] != "Renamed Folder":
    print(f"❌ Name mismatch: {folder['name']}")
    exit(1)

print(f"✅ Renamed to: {folder['name']}")

# Verify persistence
print("\nVerifying...")
response = requests.get(
    f"{BASE_URL}/api/diagrams/folders/{folder_id}",
    headers=headers,
    verify=False
)

if response.status_code != 200:
    print(f"Get failed: {response.status_code} - {response.text}")
    exit(1)

folder = response.json()
if folder["name"] != "Renamed Folder":
    print(f"❌ Name not persisted: {folder['name']}")
    exit(1)

print(f"✅ Name persisted: {folder['name']}")

# Cleanup
requests.delete(f"{BASE_URL}/api/diagrams/folders/{folder_id}", headers=headers, verify=False)

print("\n✅ Feature #580 PASSED!")
