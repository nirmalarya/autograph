import requests
import json

headers = {"X-User-ID": "test-user-123"}
resp = requests.get("http://localhost:8082/icons/search", params={"limit": 1}, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response type: {type(resp.json())}")
print(f"Response: {json.dumps(resp.json(), indent=2)[:500]}")
