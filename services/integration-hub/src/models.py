"""Database models for integration hub."""
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class WebhookBase(BaseModel):
    """Base webhook model."""
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: bool = True

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        if len(v) > 2048:
            raise ValueError('URL too long (max 2048 characters)')
        return v

    @validator('events')
    def validate_events(cls, v):
        """Validate events array."""
        if not v:
            raise ValueError('At least one event must be specified')
        allowed_events = [
            'diagram.created',
            'diagram.updated',
            'diagram.deleted',
            'comment.created',
            'comment.updated',
            'share.created'
        ]
        for event in v:
            if event not in allowed_events:
                raise ValueError(f'Invalid event type: {event}. Allowed: {", ".join(allowed_events)}')
        return v


class WebhookCreate(WebhookBase):
    """Create webhook request."""
    pass


class WebhookUpdate(BaseModel):
    """Update webhook request."""
    url: Optional[str] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None

    @validator('url')
    def validate_url(cls, v):
        """Validate URL format if provided."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            if len(v) > 2048:
                raise ValueError('URL too long (max 2048 characters)')
        return v

    @validator('events')
    def validate_events(cls, v):
        """Validate events array if provided."""
        if v is not None:
            if not v:
                raise ValueError('At least one event must be specified')
            allowed_events = [
                'diagram.created',
                'diagram.updated',
                'diagram.deleted',
                'comment.created',
                'comment.updated',
                'share.created'
            ]
            for event in v:
                if event not in allowed_events:
                    raise ValueError(f'Invalid event type: {event}. Allowed: {", ".join(allowed_events)}')
        return v


class Webhook(WebhookBase):
    """Webhook database model."""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0

    class Config:
        orm_mode = True
        from_attributes = True


class WebhookTestRequest(BaseModel):
    """Webhook test request."""
    webhook_id: UUID


class WebhookTestResponse(BaseModel):
    """Webhook test response."""
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
