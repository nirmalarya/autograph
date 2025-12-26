import requests

# Try login with form data (OAuth2 style)
response = requests.post(
    "http://localhost:8080/api/auth/login",
    data={
        "username": "svg_test_1766770843",
        "password": "Test123!"
    }
)
print(f"Form data - Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Try login with JSON
response2 = requests.post(
    "http://localhost:8080/api/auth/login",
    json={
        "username": "svg_test_1766770843",
        "password": "Test123!"
    }
)
print(f"\nJSON - Status: {response2.status_code}")
print(f"Response: {response2.text[:200]}")
