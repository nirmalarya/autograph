#!/usr/bin/env python3
"""Test fuzzy query generation."""
import requests

API_URL = "http://localhost:8080/api"

# Use an existing user
response = requests.post(f"{API_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})

if response.status_code == 200:
    data = response.json()
    access_token = data.get('access_token')

    import jwt
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded.get("sub")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }

    # Test search with typo
    print("Testing search with 'Architecure' (typo)...")
    response = requests.get(
        f"{API_URL}/diagrams",
        headers=headers,
        params={"search": "Architecure"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data['diagrams'])} diagrams")
        for d in data['diagrams']:
            print(f"  - {d['title']}")
    else:
        print(f"Error: {response.text}")
else:
    print("Login failed, trying to register...")
    # Register test user
    response = requests.post(f"{API_URL}/auth/register", json={
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    })
    print(f"Register: {response.status_code}")
