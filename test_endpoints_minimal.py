#!/usr/bin/env python3
import requests

headers = {"X-User-ID": "test-user-123"}
base = "http://localhost:8082"

# Test recent
print("Testing /icons/recent...")
resp = requests.get(f"{base}/icons/recent", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

# Test favorites
print("\nTesting /icons/favorites...")
resp = requests.get(f"{base}/icons/favorites", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

# Get an icon to use
print("\nGetting an icon...")
resp = requests.get(f"{base}/icons/search", params={"limit": 1}, headers=headers)
if resp.status_code == 200:
    data = resp.json()
    icons = data.get('icons', [])
    if icons:
        icon_id = icons[0]['id']
        print(f"Icon ID: {icon_id}")

        # Test use
        print(f"\nTesting POST /icons/{icon_id}/use...")
        resp = requests.post(f"{base}/icons/{icon_id}/use", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")

        # Test recent again
        print("\nTesting /icons/recent again...")
        resp = requests.get(f"{base}/icons/recent", headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Recent icons: {len(resp.json())}")
