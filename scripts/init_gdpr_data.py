#!/usr/bin/env python3
"""
Initialize GDPR data processing activities.
Populates the data_processing_activities table with Autograph's processing activities.
"""
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Change to parent directory for imports
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from services.auth_service.src.database import SessionLocal
from services.auth_service.src.models import DataProcessingActivity

def init_processing_activities():
    """Initialize data processing activities for GDPR Article 30 compliance."""
    db = SessionLocal()

    try:
        print("Initializing GDPR data processing activities...")

        activities = [
            {
                "activity_name": "User Authentication and Authorization",
                "activity_description": "Processing user credentials and session data for authentication and authorization purposes",
                "purpose": "To authenticate users and authorize access to application features",
                "legal_basis": "contract",
                "data_categories": ["email", "password_hash", "user_id", "session_tokens", "ip_address"],
                "data_subjects": ["registered_users"],
                "recipients": ["internal_systems"],
                "third_country_transfers": False,
                "retention_period": "Duration of account plus 30 days after deletion request",
                "security_measures": "Password hashing (bcrypt), TLS 1.3 encryption, JWT tokens, MFA support, rate limiting",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            },
            {
                "activity_name": "Diagram and File Storage",
                "activity_description": "Storage and processing of user-created diagrams, files, and related metadata",
                "purpose": "To provide diagram creation and storage services to users",
                "legal_basis": "contract",
                "data_categories": ["file_content", "metadata", "user_id", "timestamps", "version_history"],
                "data_subjects": ["registered_users"],
                "recipients": ["internal_systems", "minio_storage"],
                "third_country_transfers": False,
                "retention_period": "Duration of account or until user deletes file",
                "security_measures": "Encrypted storage, access control, audit logging, backup encryption",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            },
            {
                "activity_name": "Collaboration and Comments",
                "activity_description": "Processing user comments, mentions, and collaboration data",
                "purpose": "To enable team collaboration features",
                "legal_basis": "contract",
                "data_categories": ["comments", "user_id", "mentions", "reactions", "timestamps"],
                "data_subjects": ["registered_users", "team_members"],
                "recipients": ["internal_systems", "team_members"],
                "third_country_transfers": False,
                "retention_period": "Duration of associated file or account",
                "security_measures": "Access control, permission-based visibility, audit logging",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            },
            {
                "activity_name": "Usage Analytics",
                "activity_description": "Collection of usage metrics for service improvement and billing",
                "purpose": "To improve service quality and track usage for billing purposes",
                "legal_basis": "legitimate_interest",
                "data_categories": ["metric_type", "metric_value", "user_id", "timestamps"],
                "data_subjects": ["registered_users"],
                "recipients": ["internal_systems", "analytics_team"],
                "third_country_transfers": False,
                "retention_period": "12 months",
                "security_measures": "Aggregation, access control, encrypted storage",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            },
            {
                "activity_name": "Audit Logging and Security",
                "activity_description": "Recording user actions and security events for compliance and security purposes",
                "purpose": "To ensure security, detect fraud, and comply with legal obligations",
                "legal_basis": "legal_obligation",
                "data_categories": ["action", "user_id", "ip_address", "user_agent", "timestamps"],
                "data_subjects": ["registered_users"],
                "recipients": ["internal_systems", "security_team"],
                "third_country_transfers": False,
                "retention_period": "7 years (legal requirement)",
                "security_measures": "Write-only logs, encrypted storage, access control, tamper detection",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            },
            {
                "activity_name": "Marketing Communications",
                "activity_description": "Sending marketing emails and product updates to users",
                "purpose": "To inform users about new features and service updates",
                "legal_basis": "consent",
                "data_categories": ["email", "full_name", "preferences"],
                "data_subjects": ["registered_users"],
                "recipients": ["internal_systems", "email_service_provider"],
                "third_country_transfers": True,
                "third_countries": ["United States"],
                "safeguards": "Standard Contractual Clauses (SCCs), email provider GDPR compliance certification",
                "retention_period": "Until consent is withdrawn",
                "security_measures": "Encrypted transmission, double opt-in, easy unsubscribe",
                "data_controller": "Autograph Platform",
                "data_protection_officer": "dpo@autograph.example.com"
            }
        ]

        count = 0
        for activity_data in activities:
            # Check if activity already exists
            existing = db.query(DataProcessingActivity).filter(
                DataProcessingActivity.activity_name == activity_data["activity_name"]
            ).first()

            if not existing:
                activity = DataProcessingActivity(**activity_data)
                db.add(activity)
                count += 1
                print(f"  ✅ Added: {activity_data['activity_name']}")
            else:
                print(f"  ⏭️  Skipped (exists): {activity_data['activity_name']}")

        db.commit()
        print(f"\n✅ Successfully initialized {count} data processing activities")

    except Exception as e:
        print(f"❌ Error initializing activities: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_processing_activities()
