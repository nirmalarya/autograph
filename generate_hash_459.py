#!/usr/bin/env python3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = "Test123!@#"
hashed = pwd_context.hash(password)
print(hashed)
