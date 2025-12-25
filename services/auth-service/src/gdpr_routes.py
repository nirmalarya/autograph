"""
GDPR Compliance API Routes
Endpoints for GDPR compliance: data export, deletion, consent management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

from .database import get_db
from .models import User, AuditLog
from .gdpr_service import GDPRService

# Create router
router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


# Pydantic models for requests/responses
class ConsentRequest(BaseModel):
    consent_type: str
    consent_given: bool
    consent_version: Optional[str] = None


class ConsentWithdrawRequest(BaseModel):
    consent_type: str


class DeletionRequest(BaseModel):
    reason: Optional[str] = None


class DeletionVerifyRequest(BaseModel):
    verification_token: str


class BreachLogRequest(BaseModel):
    breach_type: str
    severity: str
    description: str
    affected_users_count: int
    affected_data_categories: List[str]
    detected_at: datetime
    reported_by: str


# Dependency to get current user from JWT (simplified - should match auth service implementation)
def get_current_user_simple(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user from request. Simplified for GDPR routes."""
    # In production, this would decode JWT from Authorization header
    # For now, we'll extract user_id from a test header or query param
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# GDPR Endpoints
@router.get("/export", summary="Export User Data (Right to Access)")
async def export_user_data(
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Export all user data in JSON format (GDPR Article 15 - Right to Access).

    Returns comprehensive export of all personal data associated with the user.
    """
    try:
        export_data = GDPRService.export_user_data(current_user.id, db)

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="data_export",
            resource_type="gdpr",
            resource_id=current_user.id,
            extra_data={"export_size_bytes": len(str(export_data))}
        )
        db.add(audit_entry)
        db.commit()

        return export_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export user data: {str(e)}"
        )


@router.post("/deletion/request", summary="Request Data Deletion (Right to be Forgotten)")
async def request_data_deletion(
    deletion_request: DeletionRequest,
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Request deletion of all user data (GDPR Article 17 - Right to be Forgotten).

    Creates a deletion request that must be verified before execution.
    """
    try:
        result = GDPRService.request_data_deletion(
            current_user.id,
            deletion_request.reason,
            db
        )

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="deletion_requested",
            resource_type="gdpr",
            resource_id=result["request_id"]
        )
        db.add(audit_entry)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to request deletion: {str(e)}"
        )


@router.post("/deletion/verify", summary="Verify Data Deletion Request")
async def verify_deletion_request(
    verify_request: DeletionVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a data deletion request using the verification token.

    After verification, the deletion will be processed.
    """
    try:
        result = GDPRService.verify_deletion_request(
            verify_request.verification_token,
            db
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify deletion: {str(e)}"
        )


@router.post("/deletion/execute/{request_id}", summary="Execute Data Deletion")
async def execute_data_deletion(
    request_id: str,
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Execute a verified data deletion request.

    Admin-only endpoint for processing verified deletion requests.
    """
    try:
        # Only admins can execute deletions
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin permission required"
            )

        result = GDPRService.execute_data_deletion(request_id, db)

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="deletion_executed",
            resource_type="gdpr",
            resource_id=request_id,
            extra_data={"records_deleted": result["records_deleted"]}
        )
        db.add(audit_entry)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute deletion: {str(e)}"
        )


@router.post("/consent", summary="Record User Consent")
async def record_consent(
    consent_request: ConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Record user consent for data processing.

    Tracks consent type, version, and context for GDPR compliance.
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        result = GDPRService.record_consent(
            current_user.id,
            consent_request.consent_type,
            consent_request.consent_given,
            consent_request.consent_version,
            ip_address,
            user_agent,
            db
        )

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="consent_recorded",
            resource_type="gdpr",
            resource_id=result["consent_id"],
            extra_data={
                "consent_type": consent_request.consent_type,
                "consent_given": consent_request.consent_given
            }
        )
        db.add(audit_entry)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record consent: {str(e)}"
        )


@router.post("/consent/withdraw", summary="Withdraw Consent")
async def withdraw_consent(
    withdraw_request: ConsentWithdrawRequest,
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Withdraw previously given consent.

    Marks the consent as withdrawn with timestamp.
    """
    try:
        result = GDPRService.withdraw_consent(
            current_user.id,
            withdraw_request.consent_type,
            db
        )

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="consent_withdrawn",
            resource_type="gdpr",
            resource_id=result["consent_id"],
            extra_data={"consent_type": withdraw_request.consent_type}
        )
        db.add(audit_entry)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to withdraw consent: {str(e)}"
        )


@router.get("/consent", summary="Get User Consents")
async def get_user_consents(
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get all consents for the current user.

    Returns list of all consent records with their status.
    """
    try:
        consents = GDPRService.get_user_consents(current_user.id, db)
        return {"consents": consents}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get consents: {str(e)}"
        )


@router.post("/breach/log", summary="Log Data Breach")
async def log_data_breach(
    breach_request: BreachLogRequest,
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Log a data breach (GDPR Article 33/34).

    Admin-only endpoint for logging data breaches. DPA notification required within 72 hours.
    """
    try:
        # Only admins can log breaches
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin permission required"
            )

        result = GDPRService.log_data_breach(
            breach_request.breach_type,
            breach_request.severity,
            breach_request.description,
            breach_request.affected_users_count,
            breach_request.affected_data_categories,
            breach_request.detected_at,
            breach_request.reported_by,
            db
        )

        # Log audit
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="breach_logged",
            resource_type="gdpr",
            resource_id=result["breach_id"],
            extra_data={
                "severity": breach_request.severity,
                "affected_users": breach_request.affected_users_count
            }
        )
        db.add(audit_entry)
        db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log breach: {str(e)}"
        )


@router.get("/processing-activities", summary="Get Data Processing Activities")
async def get_processing_activities(
    current_user: User = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get data processing activities (GDPR Article 30).

    Returns list of all data processing activities with legal basis and purposes.
    """
    try:
        # Only admins can view processing activities
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin permission required"
            )

        activities = GDPRService.get_data_processing_activities(db)
        return {"activities": activities}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing activities: {str(e)}"
        )
