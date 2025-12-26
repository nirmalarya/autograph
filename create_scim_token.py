"""Create a SCIM token for testing."""
import hashlib
import secrets
import psycopg2
from datetime import datetime, timezone, timedelta
import uuid

# Generate a random token
token = secrets.token_urlsafe(32)
token_hash = hashlib.sha256(token.encode()).hexdigest()
token_id = str(uuid.uuid4())

# Calculate expiration (1 year from now)
expires_at = datetime.now(timezone.utc) + timedelta(days=365)

print(f"Generated SCIM Token: {token}")
print(f"Token ID: {token_id}")
print(f"Token Hash: {token_hash}")
print(f"Expires: {expires_at}")

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="autograph",
    user="autograph",
    password="autograph_dev_password"
)

cur = conn.cursor()

# Insert token
cur.execute("""
    INSERT INTO scim_tokens (id, token_hash, name, scopes, is_active, created_at, expires_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (
    token_id,
    token_hash,
    "Test SCIM Token",
    ["read", "write"],
    True,
    datetime.now(timezone.utc),
    expires_at
))

conn.commit()
cur.close()
conn.close()

print("\n✅ SCIM token created successfully!")
print(f"\nUse this token in your requests:")
print(f"Authorization: Bearer {token}")
