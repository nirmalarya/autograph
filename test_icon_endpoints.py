#!/usr/bin/env python3
"""Simple test of icon endpoints."""
import requests

API_BASE = "http://localhost:8080"

# Try to login with test user
print("Testing login...")
login_response = requests.post(f"{API_BASE}/auth/login", json={
    "email": "test@example.com",
    "password": "password123"
})

print(f"Login status: {login_response.status_code}")
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in successfully")

    # Test icon endpoints
    print("\nTesting icon categories...")
    cat_response = requests.get(f"{API_BASE}/icons/categories", headers=headers)
    print(f"Categories status: {cat_response.status_code}")
    if cat_response.status_code == 200:
        categories = cat_response.json()
        print(f"✅ Found {len(categories)} categories")
        total_icons = sum(c.get('icon_count', 0) for c in categories)
        print(f"Total icons: {total_icons}")
else:
    print(f"❌ Login failed: {login_response.text}")
    print("\nTrying to check database for users...")
    import subprocess
    result = subprocess.run(
        ['docker', 'exec', 'autograph-postgres', 'psql', '-U', 'autograph', '-d', 'autograph',
         '-c', 'SELECT email FROM users LIMIT 5;'],
        capture_output=True, text=True
    )
    print("Users in database:")
    print(result.stdout)
