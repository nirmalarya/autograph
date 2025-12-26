"""Push Notification Service for Web Push."""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending Web Push notifications."""

    def __init__(self):
        """Initialize push notification service with VAPID keys."""
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
        self.vapid_subject = os.getenv("VAPID_SUBJECT", "mailto:noreply@autograph.dev")

        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("VAPID keys not configured - push notifications will not work")

    async def send_mention_notification(
        self,
        db: Session,
        user_id: str,
        commenter_name: str,
        comment_content: str,
        diagram_id: str,
        diagram_name: str,
        comment_id: str,
        position: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Send push notification to a user about being mentioned in a comment.

        Args:
            db: Database session
            user_id: ID of the user to notify
            commenter_name: Name of the person who mentioned the user
            comment_content: Content of the comment
            diagram_id: ID of the diagram
            diagram_name: Name of the diagram
            comment_id: ID of the comment
            position: Optional position data for the comment

        Returns:
            Number of successful notifications sent
        """
        if not self.vapid_private_key or not self.vapid_public_key:
            logger.warning("Push notifications not configured")
            return 0

        # Import here to avoid circular dependencies
        from .models import PushSubscription

        # Get all active push subscriptions for the user
        subscriptions = db.query(PushSubscription).filter(
            and_(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True
            )
        ).all()

        if not subscriptions:
            logger.info(f"No active push subscriptions for user {user_id}")
            return 0

        # Prepare notification payload
        notification_data = {
            "title": f"{commenter_name} mentioned you",
            "body": comment_content[:100] + ("..." if len(comment_content) > 100 else ""),
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/icon-96x96.png",
            "tag": f"mention-{comment_id}",
            "requireInteraction": False,
            "data": {
                "url": f"/canvas/{diagram_id}",
                "diagram_id": diagram_id,
                "diagram_name": diagram_name,
                "comment_id": comment_id,
                "commenter_name": commenter_name,
                "position": position
            },
            "actions": [
                {
                    "action": "view",
                    "title": "View Comment"
                },
                {
                    "action": "dismiss",
                    "title": "Dismiss"
                }
            ]
        }

        sent_count = 0
        failed_subscriptions = []

        # Send to all subscriptions
        for subscription in subscriptions:
            try:
                # Prepare subscription info for pywebpush
                subscription_info = {
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth
                    }
                }

                # Send the push notification
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(notification_data),
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims={
                        "sub": self.vapid_subject
                    }
                )

                sent_count += 1
                logger.info(
                    f"Push notification sent successfully",
                    extra={
                        "user_id": user_id,
                        "subscription_id": subscription.id,
                        "comment_id": comment_id
                    }
                )

            except WebPushException as e:
                logger.error(
                    f"Failed to send push notification",
                    extra={
                        "user_id": user_id,
                        "subscription_id": subscription.id,
                        "error": str(e),
                        "status_code": e.response.status_code if e.response else None
                    }
                )

                # If subscription is invalid (410 Gone or 404 Not Found), mark it as inactive
                if e.response and e.response.status_code in [410, 404]:
                    failed_subscriptions.append(subscription.id)

            except Exception as e:
                logger.error(
                    f"Unexpected error sending push notification",
                    extra={
                        "user_id": user_id,
                        "subscription_id": subscription.id,
                        "error": str(e)
                    }
                )

        # Deactivate failed subscriptions
        if failed_subscriptions:
            db.query(PushSubscription).filter(
                PushSubscription.id.in_(failed_subscriptions)
            ).update({"is_active": False}, synchronize_session=False)
            db.commit()
            logger.info(f"Deactivated {len(failed_subscriptions)} invalid push subscriptions")

        return sent_count


# Singleton instance
_push_service = None


def get_push_notification_service() -> PushNotificationService:
    """Get or create the push notification service instance."""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service
