#!/usr/bin/env python3
"""Setup test user for Feature #445."""
import hashlib
import subprocess

PASSWORD = "Test123!"
EMAIL = "test_user_445@example.com"

# Generate SHA256 hash
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()

print(f"Password: {PASSWORD}")
print(f"Hash: {password_hash}")

# Create SQL command
sql_commands = f"""
DELETE FROM users WHERE email = '{EMAIL}';

INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'test-user-445',
    '{EMAIL}',
    '{password_hash}',
    'Test User 445',
    'user',
    true,
    true,
    NOW(),
    NOW()
);
"""

# Execute SQL
result = subprocess.run(
    ['docker', 'exec', '-i', 'autograph-postgres', 'psql', '-U', 'autograph', '-d', 'autograph'],
    input=sql_commands.encode(),
    capture_output=True
)

if result.returncode == 0:
    print(f"\n✅ User created successfully!")
    print(f"   Email: {EMAIL}")
    print(f"   Password: {PASSWORD}")
else:
    print(f"\n❌ Failed: {result.stderr.decode()}")
