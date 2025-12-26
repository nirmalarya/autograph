"""SCIM 2.0 provisioning routes for enterprise user sync."""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .database import get_db
from .models import User, SCIMToken
import bcrypt

router = APIRouter(prefix="/scim/v2", tags=["SCIM"])


# ================================================================================
# SCIM AUTHENTICATION
# ================================================================================

async def verify_scim_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> SCIMToken:
    """Verify SCIM bearer token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    scim_token = db.query(SCIMToken).filter(
        SCIMToken.token_hash == token_hash,
        SCIMToken.is_active == True
    ).first()

    if not scim_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration
    if scim_token.expires_at and scim_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last used
    scim_token.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return scim_token


# ================================================================================
# SCIM SCHEMAS
# ================================================================================

class SCIMMeta(BaseModel):
    """SCIM metadata."""
    resourceType: str
    created: Optional[str] = None
    lastModified: Optional[str] = None
    location: Optional[str] = None


class SCIMName(BaseModel):
    """SCIM name structure."""
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None


class SCIMEmail(BaseModel):
    """SCIM email structure."""
    value: EmailStr
    type: Optional[str] = "work"
    primary: Optional[bool] = True


class SCIMUserCreate(BaseModel):
    """SCIM user creation request."""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    externalId: Optional[str] = None
    userName: EmailStr  # Required by SCIM 2.0
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    emails: List[SCIMEmail]
    active: bool = True


class SCIMUserUpdate(BaseModel):
    """SCIM user update request."""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    externalId: Optional[str] = None
    userName: Optional[EmailStr] = None
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    emails: Optional[List[SCIMEmail]] = None
    active: Optional[bool] = None


class SCIMUserResponse(BaseModel):
    """SCIM user response."""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    id: str
    externalId: Optional[str] = None
    userName: str
    name: Optional[SCIMName] = None
    displayName: Optional[str] = None
    emails: List[SCIMEmail]
    active: bool
    meta: SCIMMeta

    class Config:
        from_attributes = True


class SCIMListResponse(BaseModel):
    """SCIM list response."""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: List[SCIMUserResponse]


class SCIMError(BaseModel):
    """SCIM error response."""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    detail: str
    status: int


# ================================================================================
# SCIM ENDPOINTS
# ================================================================================

@router.get("/ServiceProviderConfig")
async def get_service_provider_config(token: SCIMToken = Depends(verify_scim_token)):
    """Get SCIM service provider configuration."""
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "documentationUri": "https://autograph.ai/docs/scim",
        "patch": {
            "supported": True
        },
        "bulk": {
            "supported": False,
            "maxOperations": 0,
            "maxPayloadSize": 0
        },
        "filter": {
            "supported": True,
            "maxResults": 200
        },
        "changePassword": {
            "supported": False
        },
        "sort": {
            "supported": True
        },
        "etag": {
            "supported": False
        },
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "specUri": "https://www.rfc-editor.org/info/rfc6750",
                "documentationUri": "https://autograph.ai/docs/scim/auth",
                "primary": True
            }
        ],
        "meta": {
            "resourceType": "ServiceProviderConfig",
            "location": "/scim/v2/ServiceProviderConfig"
        }
    }


@router.get("/ResourceTypes")
async def get_resource_types(token: SCIMToken = Depends(verify_scim_token)):
    """Get supported SCIM resource types."""
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 1,
        "Resources": [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/scim/v2/Users",
                "description": "User Account",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                "meta": {
                    "resourceType": "ResourceType",
                    "location": "/scim/v2/ResourceTypes/User"
                }
            }
        ]
    }


@router.get("/Schemas")
async def get_schemas(token: SCIMToken = Depends(verify_scim_token)):
    """Get SCIM schemas."""
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 1,
        "Resources": [
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                "name": "User",
                "description": "User Account",
                "attributes": [
                    {
                        "name": "userName",
                        "type": "string",
                        "multiValued": False,
                        "required": True,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "server"
                    },
                    {
                        "name": "name",
                        "type": "complex",
                        "multiValued": False,
                        "required": False,
                        "mutability": "readWrite",
                        "returned": "default"
                    },
                    {
                        "name": "emails",
                        "type": "complex",
                        "multiValued": True,
                        "required": True,
                        "mutability": "readWrite",
                        "returned": "default"
                    },
                    {
                        "name": "active",
                        "type": "boolean",
                        "multiValued": False,
                        "required": False,
                        "mutability": "readWrite",
                        "returned": "default"
                    }
                ],
                "meta": {
                    "resourceType": "Schema",
                    "location": "/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User"
                }
            }
        ]
    }


@router.post("/Users", response_model=SCIMUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: SCIMUserCreate,
    db: Session = Depends(get_db),
    token: SCIMToken = Depends(verify_scim_token)
):
    """Create a new user via SCIM."""
    # Check if user already exists
    email = user_data.emails[0].value if user_data.emails else user_data.userName

    existing_user = db.query(User).filter(
        or_(
            User.email == email,
            User.scim_external_id == user_data.externalId
        )
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or externalId already exists"
        )

    # Generate random password for SCIM-provisioned users
    random_password = secrets.token_urlsafe(32)
    password_hash = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Extract name parts
    full_name = user_data.displayName
    if user_data.name:
        if user_data.name.formatted:
            full_name = user_data.name.formatted
        elif user_data.name.givenName and user_data.name.familyName:
            full_name = f"{user_data.name.givenName} {user_data.name.familyName}"
        elif user_data.name.givenName:
            full_name = user_data.name.givenName

    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        is_active=user_data.active,
        is_verified=True,  # SCIM users are pre-verified
        scim_external_id=user_data.externalId,
        scim_active=user_data.active,
        sso_provider="scim",
        scim_meta={
            "resourceType": "User",
            "created": datetime.now(timezone.utc).isoformat(),
            "lastModified": datetime.now(timezone.utc).isoformat()
        }
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Build response
    name_obj = None
    if full_name:
        parts = full_name.split(" ", 1)
        name_obj = SCIMName(
            formatted=full_name,
            givenName=parts[0] if len(parts) > 0 else None,
            familyName=parts[1] if len(parts) > 1 else None
        )

    return SCIMUserResponse(
        id=user.id,
        externalId=user.scim_external_id,
        userName=user.email,
        name=name_obj,
        displayName=user.full_name,
        emails=[SCIMEmail(value=user.email, type="work", primary=True)],
        active=user.scim_active or user.is_active,
        meta=SCIMMeta(
            resourceType="User",
            created=user.created_at.isoformat() if user.created_at else None,
            lastModified=user.updated_at.isoformat() if user.updated_at else None,
            location=f"/scim/v2/Users/{user.id}"
        )
    )


@router.get("/Users/{user_id}", response_model=SCIMUserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    token: SCIMToken = Depends(verify_scim_token)
):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build name object
    name_obj = None
    if user.full_name:
        parts = user.full_name.split(" ", 1)
        name_obj = SCIMName(
            formatted=user.full_name,
            givenName=parts[0] if len(parts) > 0 else None,
            familyName=parts[1] if len(parts) > 1 else None
        )

    return SCIMUserResponse(
        id=user.id,
        externalId=user.scim_external_id,
        userName=user.email,
        name=name_obj,
        displayName=user.full_name,
        emails=[SCIMEmail(value=user.email, type="work", primary=True)],
        active=user.scim_active if user.scim_active is not None else user.is_active,
        meta=SCIMMeta(
            resourceType="User",
            created=user.created_at.isoformat() if user.created_at else None,
            lastModified=user.updated_at.isoformat() if user.updated_at else None,
            location=f"/scim/v2/Users/{user.id}"
        )
    )


@router.get("/Users", response_model=SCIMListResponse)
async def list_users(
    startIndex: int = 1,
    count: int = 100,
    filter: Optional[str] = None,
    db: Session = Depends(get_db),
    token: SCIMToken = Depends(verify_scim_token)
):
    """List users with pagination and filtering."""
    query = db.query(User)

    # Apply filter if provided
    if filter:
        # Simple filter parsing for common cases
        # Example: userName eq "user@example.com"
        # Example: externalId eq "12345"
        if "userName eq" in filter:
            email = filter.split('"')[1]
            query = query.filter(User.email == email)
        elif "externalId eq" in filter:
            external_id = filter.split('"')[1]
            query = query.filter(User.scim_external_id == external_id)

    # Get total count
    total = query.count()

    # Apply pagination
    users = query.offset(startIndex - 1).limit(count).all()

    # Build response
    resources = []
    for user in users:
        name_obj = None
        if user.full_name:
            parts = user.full_name.split(" ", 1)
            name_obj = SCIMName(
                formatted=user.full_name,
                givenName=parts[0] if len(parts) > 0 else None,
                familyName=parts[1] if len(parts) > 1 else None
            )

        resources.append(SCIMUserResponse(
            id=user.id,
            externalId=user.scim_external_id,
            userName=user.email,
            name=name_obj,
            displayName=user.full_name,
            emails=[SCIMEmail(value=user.email, type="work", primary=True)],
            active=user.scim_active if user.scim_active is not None else user.is_active,
            meta=SCIMMeta(
                resourceType="User",
                created=user.created_at.isoformat() if user.created_at else None,
                lastModified=user.updated_at.isoformat() if user.updated_at else None,
                location=f"/scim/v2/Users/{user.id}"
            )
        ))

    return SCIMListResponse(
        totalResults=total,
        startIndex=startIndex,
        itemsPerPage=len(resources),
        Resources=resources
    )


@router.put("/Users/{user_id}", response_model=SCIMUserResponse)
async def update_user(
    user_id: str,
    user_data: SCIMUserUpdate,
    db: Session = Depends(get_db),
    token: SCIMToken = Depends(verify_scim_token)
):
    """Update user via SCIM."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_data.externalId is not None:
        user.scim_external_id = user_data.externalId

    if user_data.userName:
        user.email = user_data.userName

    if user_data.emails:
        user.email = user_data.emails[0].value

    if user_data.displayName:
        user.full_name = user_data.displayName
    elif user_data.name:
        if user_data.name.formatted:
            user.full_name = user_data.name.formatted
        elif user_data.name.givenName and user_data.name.familyName:
            user.full_name = f"{user_data.name.givenName} {user_data.name.familyName}"
        elif user_data.name.givenName:
            user.full_name = user_data.name.givenName

    if user_data.active is not None:
        user.scim_active = user_data.active
        user.is_active = user_data.active

    # Update metadata
    if not user.scim_meta:
        user.scim_meta = {}
    user.scim_meta["lastModified"] = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(user)

    # Build response
    name_obj = None
    if user.full_name:
        parts = user.full_name.split(" ", 1)
        name_obj = SCIMName(
            formatted=user.full_name,
            givenName=parts[0] if len(parts) > 0 else None,
            familyName=parts[1] if len(parts) > 1 else None
        )

    return SCIMUserResponse(
        id=user.id,
        externalId=user.scim_external_id,
        userName=user.email,
        name=name_obj,
        displayName=user.full_name,
        emails=[SCIMEmail(value=user.email, type="work", primary=True)],
        active=user.scim_active if user.scim_active is not None else user.is_active,
        meta=SCIMMeta(
            resourceType="User",
            created=user.created_at.isoformat() if user.created_at else None,
            lastModified=user.updated_at.isoformat() if user.updated_at else None,
            location=f"/scim/v2/Users/{user.id}"
        )
    )


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    token: SCIMToken = Depends(verify_scim_token)
):
    """Delete/deactivate user via SCIM."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Instead of hard delete, we deactivate
    user.scim_active = False
    user.is_active = False

    db.commit()

    return None
