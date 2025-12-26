#!/usr/bin/env python3
import bcrypt

password = "TestPass123!"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(hashed.decode('utf-8'))
