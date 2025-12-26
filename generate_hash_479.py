import bcrypt

password = "SecurePass123!"
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hash.decode())
