#!/usr/bin/env python3
import bcrypt
import uuid

password = 'SecurePass123!'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
user_id = str(uuid.uuid4())
email = 'thumbnail_test_460@example.com'

print(f'-- User ID: {user_id}')
print(f'-- Email: {email}')
print(f'-- Password: {password}')
print()
print(f"INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)")
print(f"VALUES ('{user_id}', '{email}', '{hashed}', 'Thumbnail Test User 460', true, true, 'user', NOW(), NOW());")
