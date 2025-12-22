#!/usr/bin/env python3
"""Test registration endpoint directly."""
import sys
import os
sys.path.insert(0, 'src')

from sqlalchemy.orm import Session
from src.database import SessionLocal, engine
from src.models import User, Base
from src.main import get_password_hash
import uuid

# Test database connection
print("Testing database connection...")
try:
    with engine.connect() as conn:
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Test user creation
print("\nTesting user creation...")
db = SessionLocal()
try:
    # Create test user
    test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    hashed_password = get_password_hash("testpass123")
    
    print(f"Creating user with email: {test_email}")
    new_user = User(
        email=test_email,
        password_hash=hashed_password,
        full_name="Test User",
        is_active=True,
        role="user"
    )
    
    print(f"User object before add: id={getattr(new_user, 'id', 'NOT SET')}")
    
    db.add(new_user)
    print(f"User object after add: id={getattr(new_user, 'id', 'NOT SET')}")
    
    db.commit()
    print(f"User object after commit: id={new_user.id}")
    
    db.refresh(new_user)
    print(f"User object after refresh: id={new_user.id}")
    
    print(f"\n✅ User created successfully!")
    print(f"   ID: {new_user.id}")
    print(f"   Email: {new_user.email}")
    print(f"   Full Name: {new_user.full_name}")
    print(f"   Role: {new_user.role}")
    print(f"   Created At: {new_user.created_at}")
    
except Exception as e:
    print(f"❌ User creation failed: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
