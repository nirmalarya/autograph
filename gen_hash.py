import bcrypt
password = b'password123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode())
