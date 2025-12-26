"""Push Notification Routes for Auth Service."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Optional
import logging
import os
from jose import JWTError, jwt

from .database import get_db
from .models import User, PushSubscription, generate_uuid

# Create router without prefix - will be added by main app
router = APIRouter(tags=["Push Notifications"])
logger = logging.getLogger("auth-service")

# OAuth2 scheme for token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-min-32-chars-long!!")
ALGORITHM = "HS256"


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception


class PushSubscriptionCreate(BaseModel):
    """Push subscription creation request."""
    endpoint: str
    keys: dict  # Contains p256dh and auth


class PushSubscriptionResponse(BaseModel):
    """Push subscription response."""
    id: str
    endpoint: str
    is_active: bool
    created_at: datetime


@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscriptionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subscribe to push notifications.

    Creates or updates a push subscription for the current user.
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    try:
        # Extract keys from subscription
        p256dh = subscription.keys.get("p256dh", "")
        auth = subscription.keys.get("auth", "")

        if not p256dh or not auth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing subscription keys (p256dh and auth required)"
            )

        # Check if subscription already exists for this endpoint
        existing_sub = db.query(PushSubscription).filter(
            PushSubscription.endpoint == subscription.endpoint
        ).first()

        if existing_sub:
            # Update existing subscription
            existing_sub.p256dh = p256dh
            existing_sub.auth = auth
            existing_sub.user_agent = request.headers.get("User-Agent", "")
            existing_sub.is_active = True
            existing_sub.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_sub)

            logger.info(
                "Push subscription updated",
                correlation_id=correlation_id,
                user_id=current_user.id,
                subscription_id=existing_sub.id
            )

            return {
                "id": existing_sub.id,
                "endpoint": existing_sub.endpoint,
                "is_active": existing_sub.is_active,
                "created_at": existing_sub.created_at
            }
        else:
            # Create new subscription
            new_sub = PushSubscription(
                id=generate_uuid(),
                user_id=current_user.id,
                endpoint=subscription.endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=request.headers.get("User-Agent", ""),
                is_active=True
            )
            db.add(new_sub)
            db.commit()
            db.refresh(new_sub)

            logger.info(
                "Push subscription created",
                correlation_id=correlation_id,
                user_id=current_user.id,
                subscription_id=new_sub.id
            )

            return {
                "id": new_sub.id,
                "endpoint": new_sub.endpoint,
                "is_active": new_sub.is_active,
                "created_at": new_sub.created_at
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create push subscription",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create push subscription"
        )


@router.post("/unsubscribe")
async def unsubscribe_from_push(
    request: Request,
    endpoint: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from push notifications.

    Deactivates a push subscription for the current user.
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    try:
        body = await request.json()
        endpoint = body.get("endpoint") or endpoint

        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Endpoint is required"
            )

        # Find subscription
        subscription = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id
        ).first()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        # Deactivate subscription
        subscription.is_active = False
        subscription.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Push subscription deactivated",
            correlation_id=correlation_id,
            user_id=current_user.id,
            subscription_id=subscription.id
        )

        return {"message": "Unsubscribed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to unsubscribe from push",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsubscribe from push"
        )


@router.get("/subscriptions")
async def get_push_subscriptions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all push subscriptions for the current user.
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")

    try:
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.is_active == True
        ).all()

        return {
            "subscriptions": [
                {
                    "id": sub.id,
                    "endpoint": sub.endpoint,
                    "user_agent": sub.user_agent,
                    "created_at": sub.created_at,
                    "last_used_at": sub.last_used_at
                }
                for sub in subscriptions
            ]
        }

    except Exception as e:
        logger.error(
            "Failed to get push subscriptions",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get push subscriptions"
        )
