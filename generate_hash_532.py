import bcrypt
password = b'testpass123'
hash_value = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
print(hash_value)
