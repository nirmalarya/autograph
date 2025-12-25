#!/usr/bin/env python3
import requests

headers = {"X-User-ID": "test-user-123"}
resp = requests.get("http://localhost:8082/icons/recent", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
print(f"Response: {resp.text}")

# Try without user ID
print("\nWithout X-User-ID:")
resp2 = requests.get("http://localhost:8082/icons/recent")
print(f"Status: {resp2.status_code}")
print(f"Response: {resp2.text}")
