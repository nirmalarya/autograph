"""Generate JWT token for test user."""
import jwt
from datetime import datetime, timedelta
import os

JWT_SECRET = os.getenv("JWT_SECRET", "autograph_jwt_secret_key_change_in_production")
user_id = "test-webhook-558"

payload = {
    "user_id": user_id,
    "sub": user_id,
    "email": "webhook-test@autograph.com",
    "exp": datetime.utcnow() + timedelta(hours=24),
    "iat": datetime.utcnow()
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
print(token)
