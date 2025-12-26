#!/usr/bin/env python3
import bcrypt
password = 'SecurePass123!'.encode('utf-8')
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)
print(hashed.decode('utf-8'))
