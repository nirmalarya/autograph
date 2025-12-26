"""Webhook management endpoints."""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import List, Optional
from uuid import UUID
import jwt
import os
import httpx
from datetime import datetime
import hmac
import hashlib
import json

from ..models import (
    Webhook,
    WebhookCreate,
    WebhookUpdate,
    WebhookTestRequest,
    WebhookTestResponse
)
from ..database import get_db_cursor

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# JWT Secret for token validation
JWT_SECRET = os.getenv("JWT_SECRET", "autograph_jwt_secret_key_change_in_production")


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user_id from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def check_enterprise_user(user_id: str) -> bool:
    """Check if user has enterprise plan."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT plan FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return result['plan'] == 'enterprise'


@router.post("", response_model=Webhook, status_code=201)
async def create_webhook(
    webhook: WebhookCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new webhook. Enterprise only."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO webhooks (user_id, url, events, secret, active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, user_id, url, events, secret, active, created_at, updated_at, last_triggered_at, failure_count
            """,
            (user_id, webhook.url, webhook.events, webhook.secret, webhook.active)
        )
        result = cursor.fetchone()
        return dict(result)


@router.get("", response_model=List[Webhook])
async def list_webhooks(user_id: str = Depends(get_current_user)):
    """List all webhooks for the current user."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, url, events, secret, active, created_at, updated_at, last_triggered_at, failure_count
            FROM webhooks
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        results = cursor.fetchall()
        return [dict(row) for row in results]


@router.get("/{webhook_id}", response_model=Webhook)
async def get_webhook(
    webhook_id: UUID,
    user_id: str = Depends(get_current_user)
):
    """Get a specific webhook."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, url, events, secret, active, created_at, updated_at, last_triggered_at, failure_count
            FROM webhooks
            WHERE id = %s AND user_id = %s
            """,
            (str(webhook_id), user_id)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return dict(result)


@router.put("/{webhook_id}", response_model=Webhook)
async def update_webhook(
    webhook_id: UUID,
    webhook: WebhookUpdate,
    user_id: str = Depends(get_current_user)
):
    """Update a webhook."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    # Build dynamic update query
    update_fields = []
    params = []

    if webhook.url is not None:
        update_fields.append("url = %s")
        params.append(webhook.url)
    if webhook.events is not None:
        update_fields.append("events = %s")
        params.append(webhook.events)
    if webhook.secret is not None:
        update_fields.append("secret = %s")
        params.append(webhook.secret)
    if webhook.active is not None:
        update_fields.append("active = %s")
        params.append(webhook.active)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.extend([str(webhook_id), user_id])

    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE webhooks
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, url, events, secret, active, created_at, updated_at, last_triggered_at, failure_count
            """,
            tuple(params)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return dict(result)


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: UUID,
    user_id: str = Depends(get_current_user)
):
    """Delete a webhook."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    with get_db_cursor() as cursor:
        cursor.execute(
            "DELETE FROM webhooks WHERE id = %s AND user_id = %s",
            (str(webhook_id), user_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/test", response_model=WebhookTestResponse)
async def test_webhook(
    test_request: WebhookTestRequest,
    user_id: str = Depends(get_current_user)
):
    """Test a webhook by sending a test payload."""
    # Check if user is enterprise
    if not check_enterprise_user(user_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook management is only available for enterprise users"
        )

    # Get webhook details
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, url, events, secret, active
            FROM webhooks
            WHERE id = %s AND user_id = %s
            """,
            (str(test_request.webhook_id), user_id)
        )
        webhook = cursor.fetchone()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

    # Prepare test payload
    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook delivery from AutoGraph",
            "webhook_id": str(webhook['id'])
        }
    }

    # Send webhook
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            headers = {"Content-Type": "application/json"}

            # Add HMAC signature if secret is configured
            if webhook['secret']:
                signature = hmac.new(
                    webhook['secret'].encode(),
                    json.dumps(test_payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            response = await client.post(
                webhook['url'],
                json=test_payload,
                headers=headers
            )

            # Log delivery
            with get_db_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO webhook_deliveries (webhook_id, event_type, payload, response_status, response_body, success)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(webhook['id']),
                        'webhook.test',
                        json.dumps(test_payload),
                        response.status_code,
                        response.text[:1000],  # Truncate response
                        200 <= response.status_code < 300
                    )
                )

            return WebhookTestResponse(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_body=response.text[:500]  # Truncate for response
            )

    except httpx.TimeoutException:
        return WebhookTestResponse(
            success=False,
            error="Request timeout (10 seconds)"
        )
    except httpx.RequestError as e:
        return WebhookTestResponse(
            success=False,
            error=f"Request failed: {str(e)}"
        )
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )
