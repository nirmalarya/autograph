import requests
import time

username = f"svg_test_{int(time.time())}"
password = "Test123!"

# Try via API gateway
print("Testing via API Gateway...")
response = requests.post(
    "http://localhost:8080/api/auth/register",
    json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
