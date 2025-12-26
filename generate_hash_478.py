#!/usr/bin/env python3
import bcrypt

password = "TestPassword123!"
hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Password: {password}")
print(f"Hash: {hash}")
