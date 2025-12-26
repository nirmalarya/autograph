#!/usr/bin/env python3
"""Generate VAPID keys for Web Push notifications."""

from vapid import Vapid

# Generate new VAPID keys
vapid = Vapid()
vapid.generate_keys()

# Print the keys
print("=" * 80)
print("VAPID Keys Generated Successfully")
print("=" * 80)
print("\nAdd these to your .env file:\n")
print(f"VAPID_PRIVATE_KEY={vapid.private_key_pem().decode()}")
print(f"VAPID_PUBLIC_KEY={vapid.public_key_urlsafe().decode()}")
print("\n" + "=" * 80)
