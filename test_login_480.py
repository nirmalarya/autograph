#!/usr/bin/env python3
import requests
import json

response = requests.post("http://localhost:8085/login", json={
    "email": "compress480@test.com",
    "password": "SecurePass123!"
})

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
