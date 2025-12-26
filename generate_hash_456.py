#!/usr/bin/env python3
import bcrypt

password = "TestPassword123!"
salt = bcrypt.gensalt()
hash_value = bcrypt.hashpw(password.encode('utf-8'), salt)
print(hash_value.decode('utf-8'))
