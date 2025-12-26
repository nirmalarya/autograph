import bcrypt

password = "test458pass"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
print(hashed.decode('utf-8'))
