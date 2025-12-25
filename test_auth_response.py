import requests
import time

timestamp = int(time.time())
email = f"test_profile_{timestamp}@test.com"

# Register
r = requests.post('http://localhost:8080/api/auth/register', json={
    'email': email,
    'password': 'Test123!',
    'name': 'Test User'
})
print("Registration response:")
print(r.json())
print()

# Login
r = requests.post('http://localhost:8080/api/auth/login', json={
    'email': email,
    'password': 'Test123!'
})
login_data = r.json()
print("Login response:")
print(login_data)
print()

# Get profile
token = login_data.get('access_token')
r = requests.get('http://localhost:8080/api/auth/profile', headers={
    'Authorization': f'Bearer {token}'
})
print("Profile response:")
print(r.json())
