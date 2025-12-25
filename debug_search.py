import requests
import json

headers = {"X-User-ID": "test123"}
resp = requests.get("http://localhost:8082/icons/search", params={"q": "aws", "limit": 2}, headers=headers)
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Type: {type(data)}")
print(f"Data: {json.dumps(data, indent=2)[:500]}")
