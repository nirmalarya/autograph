#!/usr/bin/env python3
"""Create GDPR tables"""
import sys
sys.path.insert(0, '/app')

from src.database import engine
from src.models import UserConsent, DataProcessingActivity, DataBreachLog, DataDeletionRequest, Base

print("Creating GDPR tables...")
Base.metadata.create_all(bind=engine, tables=[
    UserConsent.__table__,
    DataProcessingActivity.__table__,
    DataBreachLog.__table__,
    DataDeletionRequest.__table__,
])
print("✅ GDPR tables created successfully!")
