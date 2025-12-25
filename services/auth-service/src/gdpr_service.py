"""
GDPR Compliance Service
Implements GDPR requirements: data export, deletion, consent management, breach notification
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Optional, Any
import json
import secrets

from .models import (
    User, UserConsent, DataProcessingActivity, DataBreachLog, DataDeletionRequest,
    File, Version, Comment, Team, TeamMember, Folder, Share, GitConnection,
    AuditLog, ApiKey, UsageMetric, RefreshToken, PasswordResetToken,
    EmailVerificationToken, OAuthApp, OAuthAuthorizationCode, OAuthAccessToken,
    Mention, CommentReaction
)


class GDPRService:
    """Service for GDPR compliance operations."""

    @staticmethod
    def export_user_data(user_id: str, db: Session) -> Dict[str, Any]:
        """
        Export all user data (GDPR Article 15 - Right to Access).
        Returns comprehensive JSON export of all user data.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        export_data = {
            "export_metadata": {
                "exported_at": datetime.now(dt_timezone.utc).isoformat(),
                "user_id": user_id,
                "export_version": "1.0",
                "gdpr_article": "Article 15 - Right to Access"
            },
            "personal_data": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "sso_provider": user.sso_provider,
                "mfa_enabled": user.mfa_enabled,
                "preferences": user.preferences,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            },
            "files": [
                {
                    "id": f.id,
                    "title": f.title,
                    "file_type": f.file_type,
                    "is_starred": f.is_starred,
                    "tags": f.tags,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in user.files
            ],
            "comments": [
                {
                    "id": c.id,
                    "file_id": c.file_id,
                    "content": c.content,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in user.comments
            ],
            "teams": [
                {
                    "id": t.id,
                    "name": t.name,
                    "slug": t.slug,
                    "plan": t.plan,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in user.teams
            ],
            "folders": [
                {
                    "id": f.id,
                    "name": f.name,
                    "color": f.color,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in user.folders
            ],
            "git_connections": [
                {
                    "id": g.id,
                    "provider": g.provider,
                    "repository_name": g.repository_name,
                    "branch": g.branch,
                    "auto_sync": g.auto_sync,
                    "created_at": g.created_at.isoformat() if g.created_at else None,
                }
                for g in user.git_connections
            ],
            "api_keys": [
                {
                    "id": a.id,
                    "name": a.name,
                    "key_prefix": a.key_prefix,
                    "scopes": a.scopes,
                    "is_active": a.is_active,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "last_used_at": a.last_used_at.isoformat() if a.last_used_at else None,
                }
                for a in user.api_keys
            ],
            "audit_logs": [
                {
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in db.query(AuditLog).filter(AuditLog.user_id == user_id).limit(100).all()
            ],
            "consents": [
                {
                    "consent_type": c.consent_type,
                    "consent_given": c.consent_given,
                    "consent_version": c.consent_version,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
                }
                for c in db.query(UserConsent).filter(UserConsent.user_id == user_id).all()
            ],
            "usage_metrics_summary": {
                "total_metrics": db.query(UsageMetric).filter(UsageMetric.user_id == user_id).count(),
                "by_type": {}  # Could be expanded to show metrics by type
            }
        }

        return export_data

    @staticmethod
    def request_data_deletion(user_id: str, reason: Optional[str], db: Session) -> Dict[str, str]:
        """
        Request user data deletion (GDPR Article 17 - Right to be Forgotten).
        Creates a deletion request with verification token.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check for existing pending request
        existing = db.query(DataDeletionRequest).filter(
            and_(
                DataDeletionRequest.user_id == user_id,
                DataDeletionRequest.status.in_(["pending", "verified", "processing"])
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Deletion request already exists with status: {existing.status}"
            )

        # Create deletion request
        verification_token = secrets.token_urlsafe(32)
        deletion_request = DataDeletionRequest(
            user_id=user_id,
            user_email=user.email,
            request_reason=reason,
            verification_token=verification_token,
            status="pending"
        )

        db.add(deletion_request)
        db.commit()

        return {
            "request_id": deletion_request.id,
            "status": "pending",
            "verification_token": verification_token,
            "message": "Deletion request created. Please verify using the token."
        }

    @staticmethod
    def verify_deletion_request(token: str, db: Session) -> Dict[str, str]:
        """Verify deletion request using token."""
        request = db.query(DataDeletionRequest).filter(
            DataDeletionRequest.verification_token == token
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="Invalid verification token")

        if request.status != "pending":
            raise HTTPException(status_code=400, detail=f"Request already {request.status}")

        request.status = "verified"
        request.verified_at = datetime.now(dt_timezone.utc)
        db.commit()

        return {
            "request_id": request.id,
            "status": "verified",
            "message": "Deletion request verified. Processing will begin shortly."
        }

    @staticmethod
    def execute_data_deletion(request_id: str, db: Session) -> Dict[str, Any]:
        """
        Execute data deletion (Right to be Forgotten).
        Deletes all user data except audit logs (for legal compliance).
        """
        request = db.query(DataDeletionRequest).filter(
            DataDeletionRequest.id == request_id
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="Deletion request not found")

        if request.status != "verified":
            raise HTTPException(status_code=400, detail="Request must be verified first")

        request.status = "processing"
        request.started_at = datetime.now(dt_timezone.utc)
        db.commit()

        user_id = request.user_id
        tables_processed = []
        total_deleted = 0

        try:
            # Delete in correct order to respect foreign key constraints

            # 1. Delete OAuth tokens and apps
            count = db.query(OAuthAccessToken).filter(OAuthAccessToken.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"oauth_access_tokens: {count}")

            count = db.query(OAuthAuthorizationCode).filter(OAuthAuthorizationCode.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"oauth_authorization_codes: {count}")

            count = db.query(OAuthApp).filter(OAuthApp.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"oauth_apps: {count}")

            # 2. Delete tokens
            count = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"refresh_tokens: {count}")

            count = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"password_reset_tokens: {count}")

            count = db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"email_verification_tokens: {count}")

            # 3. Delete API keys
            count = db.query(ApiKey).filter(ApiKey.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"api_keys: {count}")

            # 4. Delete usage metrics
            count = db.query(UsageMetric).filter(UsageMetric.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"usage_metrics: {count}")

            # 5. Delete mentions and comment reactions
            comment_ids = [c.id for c in db.query(Comment).filter(Comment.user_id == user_id).all()]
            if comment_ids:
                count = db.query(Mention).filter(Mention.comment_id.in_(comment_ids)).delete(synchronize_session=False)
                total_deleted += count
                tables_processed.append(f"mentions: {count}")

                count = db.query(CommentReaction).filter(CommentReaction.comment_id.in_(comment_ids)).delete(synchronize_session=False)
                total_deleted += count
                tables_processed.append(f"comment_reactions: {count}")

            # 6. Delete comments
            count = db.query(Comment).filter(Comment.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"comments: {count}")

            # 7. Delete versions
            file_ids = [f.id for f in db.query(File).filter(File.owner_id == user_id).all()]
            if file_ids:
                count = db.query(Version).filter(Version.file_id.in_(file_ids)).delete(synchronize_session=False)
                total_deleted += count
                tables_processed.append(f"versions: {count}")

            # 8. Delete shares
            if file_ids:
                count = db.query(Share).filter(Share.file_id.in_(file_ids)).delete(synchronize_session=False)
                total_deleted += count
                tables_processed.append(f"shares: {count}")

            # 9. Delete files
            count = db.query(File).filter(File.owner_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"files: {count}")

            # 10. Delete folders
            count = db.query(Folder).filter(Folder.owner_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"folders: {count}")

            # 11. Delete git connections
            count = db.query(GitConnection).filter(GitConnection.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"git_connections: {count}")

            # 12. Delete team memberships
            count = db.query(TeamMember).filter(TeamMember.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"team_members: {count}")

            # 13. Delete owned teams
            count = db.query(Team).filter(Team.owner_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"teams: {count}")

            # 14. Delete consents
            count = db.query(UserConsent).filter(UserConsent.user_id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"user_consents: {count}")

            # 15. Anonymize audit logs (keep for legal compliance, but remove PII)
            audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
            for log in audit_logs:
                log.user_id = None
                log.ip_address = "ANONYMIZED"
                log.user_agent = "ANONYMIZED"
                if log.extra_data:
                    log.extra_data = {"anonymized": True}
            tables_processed.append(f"audit_log: {len(audit_logs)} anonymized")

            # 16. Finally, delete the user
            count = db.query(User).filter(User.id == user_id).delete()
            total_deleted += count
            tables_processed.append(f"users: {count}")

            # Update deletion request
            request.status = "completed"
            request.completed_at = datetime.now(dt_timezone.utc)
            request.tables_processed = tables_processed
            request.records_deleted = total_deleted

            db.commit()

            return {
                "request_id": request.id,
                "status": "completed",
                "records_deleted": total_deleted,
                "tables_processed": tables_processed,
                "message": "User data deleted successfully"
            }

        except Exception as e:
            db.rollback()
            request.status = "failed"
            request.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

    @staticmethod
    def record_consent(
        user_id: str,
        consent_type: str,
        consent_given: bool,
        consent_version: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
        db: Session
    ) -> Dict[str, str]:
        """Record user consent for GDPR compliance."""
        consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            consent_given=consent_given,
            consent_version=consent_version,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_method="explicit"
        )

        db.add(consent)
        db.commit()

        return {
            "consent_id": consent.id,
            "consent_type": consent_type,
            "consent_given": consent_given,
            "recorded_at": consent.created_at.isoformat()
        }

    @staticmethod
    def withdraw_consent(user_id: str, consent_type: str, db: Session) -> Dict[str, str]:
        """Withdraw user consent."""
        # Find the most recent active consent of this type
        consent = db.query(UserConsent).filter(
            and_(
                UserConsent.user_id == user_id,
                UserConsent.consent_type == consent_type,
                UserConsent.consent_given == True,
                UserConsent.withdrawn_at == None
            )
        ).order_by(UserConsent.created_at.desc()).first()

        if not consent:
            raise HTTPException(status_code=404, detail="No active consent found")

        consent.withdrawn_at = datetime.now(dt_timezone.utc)
        db.commit()

        return {
            "consent_id": consent.id,
            "consent_type": consent_type,
            "withdrawn_at": consent.withdrawn_at.isoformat()
        }

    @staticmethod
    def get_user_consents(user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get all consents for a user."""
        consents = db.query(UserConsent).filter(UserConsent.user_id == user_id).all()

        return [
            {
                "consent_id": c.id,
                "consent_type": c.consent_type,
                "consent_given": c.consent_given,
                "consent_version": c.consent_version,
                "created_at": c.created_at.isoformat(),
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
                "is_active": c.consent_given and c.withdrawn_at is None
            }
            for c in consents
        ]

    @staticmethod
    def log_data_breach(
        breach_type: str,
        severity: str,
        description: str,
        affected_users_count: int,
        affected_data_categories: List[str],
        detected_at: datetime,
        reported_by: str,
        db: Session
    ) -> Dict[str, str]:
        """Log a data breach for GDPR Article 33/34 compliance."""
        breach = DataBreachLog(
            breach_type=breach_type,
            severity=severity,
            description=description,
            affected_users_count=affected_users_count,
            affected_data_categories=affected_data_categories,
            detected_at=detected_at,
            reported_by=reported_by,
            status="open"
        )

        db.add(breach)
        db.commit()

        return {
            "breach_id": breach.id,
            "severity": severity,
            "status": "open",
            "created_at": breach.created_at.isoformat(),
            "message": "Data breach logged. DPA notification required within 72 hours."
        }

    @staticmethod
    def get_data_processing_activities(db: Session) -> List[Dict[str, Any]]:
        """Get all data processing activities (GDPR Article 30)."""
        activities = db.query(DataProcessingActivity).filter(
            DataProcessingActivity.is_active == True
        ).all()

        return [
            {
                "id": a.id,
                "activity_name": a.activity_name,
                "purpose": a.purpose,
                "legal_basis": a.legal_basis,
                "data_categories": a.data_categories,
                "third_country_transfers": a.third_country_transfers
            }
            for a in activities
        ]
