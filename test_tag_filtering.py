#!/usr/bin/env python3
"""Test tag filtering feature"""

import requests
import json

BASE_URL = "http://localhost:8082"

# Get user ID from auth service
auth_response = requests.post("http://localhost:8085/login", json={
    "email": "tagtest@example.com",
    "password": "Test123!"
})

if auth_response.status_code != 200:
    print(f"Login failed: {auth_response.status_code}")
    print(auth_response.text)
    exit(1)

token_data = auth_response.json()
access_token = token_data.get('access_token')

# Decode JWT to get user ID
import base64
payload = access_token.split('.')[1]
# Add padding if needed
payload += '=' * (4 - len(payload) % 4)
decoded = json.loads(base64.b64decode(payload))
user_id = decoded.get('sub')
print(f"✅ Logged in as user: {user_id}")

# Create test diagrams with different tags
test_diagrams = [
    {"title": "AWS Architecture", "tags": ["aws", "cloud", "infrastructure"]},
    {"title": "Azure Setup", "tags": ["azure", "cloud"]},
    {"title": "Local Database", "tags": ["database", "local"]},
]

created_ids = []

for diagram_data in test_diagrams:
    response = requests.post(
        f"{BASE_URL}/",
        headers={"X-User-ID": user_id},
        json={
            "title": diagram_data["title"],
            "file_type": "canvas",
            "tags": diagram_data["tags"]
        }
    )
    
    if response.status_code == 200:
        diagram = response.json()
        created_ids.append(diagram['id'])
        print(f"✅ Created diagram '{diagram_data['title']}' with tags: {diagram_data['tags']}")
    else:
        print(f"❌ Failed to create diagram '{diagram_data['title']}': {response.status_code}")
        print(response.text)

# Test filtering by 'aws' tag
print("\n--- Testing filter by tag='aws' ---")
response = requests.get(
    f"{BASE_URL}/",
    headers={"X-User-ID": user_id},
    params={"search": "tag:aws"}
)

if response.status_code == 200:
    data = response.json()
    diagrams = data.get('diagrams', [])
    print(f"✅ Found {len(diagrams)} diagram(s) with tag 'aws'")
    for d in diagrams:
        print(f"   - {d['title']}: tags={d.get('tags', [])}")
    
    # Verify only AWS diagram is returned
    if len(diagrams) == 1 and diagrams[0]['title'] == 'AWS Architecture':
        print("✅ PASS: Tag filtering works correctly!")
    else:
        print("❌ FAIL: Expected only 'AWS Architecture' diagram")
else:
    print(f"❌ Failed to fetch diagrams: {response.status_code}")
    print(response.text)

# Test filtering by 'cloud' tag
print("\n--- Testing filter by tag='cloud' ---")
response = requests.get(
    f"{BASE_URL}/",
    headers={"X-User-ID": user_id},
    params={"search": "tag:cloud"}
)

if response.status_code == 200:
    data = response.json()
    diagrams = data.get('diagrams', [])
    print(f"✅ Found {len(diagrams)} diagram(s) with tag 'cloud'")
    for d in diagrams:
        print(f"   - {d['title']}: tags={d.get('tags', [])}")
    
    # Verify both AWS and Azure diagrams are returned
    if len(diagrams) == 2:
        titles = {d['title'] for d in diagrams}
        if 'AWS Architecture' in titles and 'Azure Setup' in titles:
            print("✅ PASS: Tag filtering works correctly for 'cloud' tag!")
        else:
            print(f"❌ FAIL: Expected 'AWS Architecture' and 'Azure Setup', got {titles}")
    else:
        print(f"❌ FAIL: Expected 2 diagrams, got {len(diagrams)}")
else:
    print(f"❌ Failed to fetch diagrams: {response.status_code}")
    print(response.text)

# Clean up - delete test diagrams
print("\n--- Cleaning up test diagrams ---")
for diagram_id in created_ids:
    response = requests.delete(
        f"{BASE_URL}/{diagram_id}",
        headers={"X-User-ID": user_id}
    )
    if response.status_code == 200:
        print(f"✅ Deleted diagram {diagram_id}")
    else:
        print(f"❌ Failed to delete diagram {diagram_id}")

print("\n✅ Test complete!")
