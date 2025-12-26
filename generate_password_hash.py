#!/usr/bin/env python3
from passlib.hash import bcrypt

password = "SecurePassword123!"
hash_value = bcrypt.hash(password)
print(hash_value)
