#!/usr/bin/env python3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "TestPass123!"
hashed = pwd_context.hash(password)
print(f"Password: {password}")
print(f"Hash: {hashed}")
