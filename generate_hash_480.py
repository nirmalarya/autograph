#!/usr/bin/env python3
import bcrypt

password = "SecurePass123!"
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(hashed.decode('utf-8'))
