import jwt
import requests
import json

# Login
response = requests.post(
    "http://localhost:8085/login",
    json={
        "email": "test_feature_455@example.com",
        "password": "SecurePass123!"
    }
)

token = response.json()["access_token"]

# Decode without verification (just to see the payload)
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"User ID: {decoded['sub']}")
print(f"Email: {decoded['email']}")
print(f"Role: {decoded['role']}")
