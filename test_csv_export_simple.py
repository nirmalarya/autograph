#!/usr/bin/env python3
import requests

# Login
resp = requests.post('http://localhost:8080/api/auth/login', json={
    'email': 'debug_csv_test@test.com',
    'password': 'TestPass123!@#'
})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test CSV export
export_resp = requests.get(
    'http://localhost:8080/api/diagrams/8c05f839-6a60-4949-8177-de137dd65ee6/comments/export/csv',
    headers=headers
)

print('Status:', export_resp.status_code)
print('Content-Type:', export_resp.headers.get('Content-Type'))
print('First 200 chars:', export_resp.text[:200])
