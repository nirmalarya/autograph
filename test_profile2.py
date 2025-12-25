import requests
import subprocess
import time

timestamp = int(time.time())
email = f"test_profile2_{timestamp}@test.com"

# Register
r = requests.post('http://localhost:8080/api/auth/register', json={
    'email': email,
    'password': 'Test123!',
    'name': 'Test User'
})
user_data = r.json()
user_id = user_data.get('id')
print(f"Registered user ID: {user_id}")

# Verify user
subprocess.run([
    "docker", "exec", "autograph-postgres",
    "psql", "-U", "autograph", "-d", "autograph",
    "-c", f"UPDATE users SET is_verified = true WHERE id = '{user_id}'"
], capture_output=True)
print("User verified")

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
profile = r.json()
print(profile)
print()
print(f"Profile user_id field: {profile.get('user_id')}")
print(f"Profile id field: {profile.get('id')}")
