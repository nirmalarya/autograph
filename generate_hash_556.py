import bcrypt
password = 'SecureAdminPass123!'.encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashed.decode('utf-8'))
