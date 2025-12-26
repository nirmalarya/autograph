#!/usr/bin/env python3
"""Update test user password for Feature #445 testing."""
import bcrypt
import subprocess

# Generate hash for the test password
password = "TestPassword445!"
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(f"Generated hash for password '{password}':")
print(password_hash)

# Update the database
sql_command = f"""
UPDATE users
SET password_hash = '{password_hash}'
WHERE email = 'realtime_user1@example.com';
"""

result = subprocess.run(
    ['docker', 'exec', '-i', 'autograph-postgres', 'psql', '-U', 'autograph', '-d', 'autograph'],
    input=sql_command.encode(),
    capture_output=True
)

if result.returncode == 0:
    print("\n✅ Password updated successfully!")
    print(f"   Email: realtime_user1@example.com")
    print(f"   Password: {password}")
else:
    print(f"\n❌ Failed to update password: {result.stderr.decode()}")
