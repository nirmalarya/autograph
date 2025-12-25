#!/usr/bin/env python3
"""
Create GDPR compliance tables directly in the database.
"""
import os
import sys
from pathlib import Path

# Add the auth-service src directory to the Python path
auth_service_src = Path(__file__).parent / "services" / "auth-service" / "src"
sys.path.insert(0, str(auth_service_src.parent))

os.chdir(Path(__file__).parent)

from src.database import engine
from src.models import (
    User, Team, TeamMember, Folder, File, Version, Comment, Mention,
    CommentReaction, Share, GitConnection, AuditLog, ApiKey, UsageMetric,
    RefreshToken, PasswordResetToken, EmailVerificationToken,
    OAuthApp, OAuthAuthorizationCode, OAuthAccessToken,
    UserConsent, DataProcessingActivity, DataBreachLog, DataDeletionRequest,
    Base
)

def create_all_tables():
    """Create all database tables including GDPR tables."""
    print("Creating all database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ All tables created successfully!")
        print("\nGDPR Tables:")
        print("  ✅ user_consents")
        print("  ✅ data_processing_activities")
        print("  ✅ data_breach_logs")
        print("  ✅ data_deletion_requests")

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_all_tables()
    sys.exit(0 if success else 1)
