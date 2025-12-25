#!/usr/bin/env python3
"""Generate a new Fernet encryption key for secrets management."""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print(key.decode())
