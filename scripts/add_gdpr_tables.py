#!/usr/bin/env python3
"""
Add GDPR compliance tables to the database.
Creates: user_consents, data_processing_activities, data_breach_logs, data_deletion_requests
"""
import sys
import os

# Add parent directory to path to import from services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.auth-service.src.database import engine, Base
from services.auth-service.src.models import (
    UserConsent,
    DataProcessingActivity,
    DataBreachLog,
    DataDeletionRequest
)

def create_gdpr_tables():
    """Create GDPR compliance tables."""
    print("Creating GDPR compliance tables...")

    # Create tables
    Base.metadata.create_all(bind=engine, tables=[
        UserConsent.__table__,
        DataProcessingActivity.__table__,
        DataBreachLog.__table__,
        DataDeletionRequest.__table__,
    ])

    print("✅ GDPR tables created successfully!")
    print("   - user_consents")
    print("   - data_processing_activities")
    print("   - data_breach_logs")
    print("   - data_deletion_requests")

if __name__ == "__main__":
    create_gdpr_tables()
