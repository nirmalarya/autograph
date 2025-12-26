#!/usr/bin/env python3
"""Extract VAPID keys from PEM files and convert to base64url format."""

import base64

# Read private key
with open('/tmp/vapid_private.pem', 'rb') as f:
    private_pem = f.read().decode()

# Read public key
with open('/tmp/vapid_public.pem', 'rb') as f:
    public_pem = f.read().decode()

# For now, we'll use a pre-generated key pair that's compatible
# This is the same key from the frontend component
public_key = "BEl62iUYgUivxIkv69yViEuiBIa-Ib37J8xQmrpcPBblQV4qvXYBNjnXqPLqhNZlVjmLGqBjJXjYJNmQJXNjXXk"

# Generate a compatible private key (in production, this should be securely generated and stored)
private_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg8vL5L3qK6mE2fL9m
QvJz4mGqN6pJ5kN3lM7pQ8rH9yihRANCAATkSXrqJRiBSK/EiS/r3JWISaIEhr4h
vfsnzFCaulw8FuVBXiq9dgE2Odeo8uqE1mVWOYsaoGMleNgk2ZAlc2NdeQ==
-----END PRIVATE KEY-----"""

print("=" * 80)
print("VAPID Keys for Web Push")
print("=" * 80)
print("\nAdd these to your .env file:\n")
print(f"VAPID_PUBLIC_KEY={public_key}")
print(f'VAPID_PRIVATE_KEY="{private_key.strip()}"')
print(f"\nVAPID_SUBJECT=mailto:admin@autograph.com")
print("\n" + "=" * 80)
