#!/usr/bin/env python3
"""Update test user for Feature #445 with proper bcrypt hash."""
import subprocess

PASSWORD = "Test123!"
EMAIL = "test_user_445@example.com"

# Generate bcrypt hash using the auth service container
print(f"Generating bcrypt hash for password: {PASSWORD}")
result = subprocess.run(
    ['docker', 'exec', 'autograph-auth-service', 'python', '-c',
     f"from passlib.hash import bcrypt; print(bcrypt.hash('{PASSWORD}'))"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Failed to generate hash: {result.stderr}")
    exit(1)

password_hash = result.stdout.strip()
print(f"Generated hash: {password_hash}")

# Update database
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

result2 = subprocess.run(
    ['docker', 'exec', '-i', 'autograph-postgres', 'psql', '-U', 'autograph', '-d', 'autograph'],
    input=sql_commands.encode(),
    capture_output=True
)

if result2.returncode == 0:
    print(f"\n✅ User created successfully!")
    print(f"   Email: {EMAIL}")
    print(f"   Password: {PASSWORD}")
else:
    print(f"\n❌ Failed: {result2.stderr.decode()}")
