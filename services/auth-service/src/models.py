"""SQLAlchemy models for all 12 database tables."""
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, 
    ForeignKey, JSON, BigInteger, Float, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


def generate_uuid():
    """Generate UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User account table."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String(512))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="user", nullable=False)  # user, admin, enterprise
    
    # SSO fields
    sso_provider = Column(String(50))  # microsoft, okta, onelogin
    sso_id = Column(String(255))

    # SCIM fields
    scim_external_id = Column(String(255))  # External ID from IdP
    scim_active = Column(Boolean, default=True)  # SCIM active status
    scim_meta = Column(JSONB, default={})  # SCIM metadata (resourceType, location, etc.)
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255))  # Base32-encoded TOTP secret
    mfa_backup_codes = Column(JSON)  # List of hashed backup codes (one-time use)
    
    # Account lockout fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))  # Account locked until this time
    
    # User preferences
    preferences = Column(JSON, default={})  # User preferences (theme, language, etc.)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True))

    # Relationships
    teams = relationship("Team", back_populates="owner")
    files = relationship("File", back_populates="owner", foreign_keys="File.owner_id")
    comments = relationship("Comment", back_populates="user", foreign_keys="Comment.user_id")
    folders = relationship("Folder", back_populates="owner")
    git_connections = relationship("GitConnection", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    usage_metrics = relationship("UsageMetric", back_populates="user")

    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_sso', 'sso_provider', 'sso_id'),
        Index('idx_users_scim_external_id', 'scim_external_id'),
    )


class Team(Base):
    """Team/organization table."""
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Team settings
    plan = Column(String(50), default="free", nullable=False)  # free, pro, enterprise
    max_members = Column(Integer, default=5)
    settings = Column(JSON, default={})
    
    # Branding
    logo_url = Column(String(512))
    custom_domain = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="teams")
    files = relationship("File", back_populates="team")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_teams_slug', 'slug'),
        Index('idx_teams_owner', 'owner_id'),
    )


class TeamMember(Base):
    """Team membership table with roles."""
    __tablename__ = "team_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="viewer", nullable=False)  # admin, editor, viewer
    
    # Invitation tracking
    invited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    invitation_status = Column(String(50), default="active", nullable=False)  # pending, active, declined
    invitation_token = Column(String(255), unique=True, index=True)
    invitation_sent_at = Column(DateTime(timezone=True))
    invitation_accepted_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        Index('idx_team_members_team', 'team_id'),
        Index('idx_team_members_user', 'user_id'),
        Index('idx_team_members_invitation_token', 'invitation_token'),
        # Unique constraint: one user can only be in a team once
        Index('idx_team_members_unique', 'team_id', 'user_id', unique=True),
    )


class Folder(Base):
    """Folder organization table."""
    __tablename__ = "folders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("folders.id", ondelete="CASCADE"))
    
    # Folder metadata
    color = Column(String(7))  # Hex color
    icon = Column(String(50))
    position = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], backref="subfolders")
    files = relationship("File", back_populates="folder")

    __table_args__ = (
        Index('idx_folders_owner', 'owner_id'),
        Index('idx_folders_parent', 'parent_id'),
    )


class File(Base):
    """Diagram/file table."""
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"))
    folder_id = Column(String(36), ForeignKey("folders.id", ondelete="SET NULL"))
    
    # File type and content
    file_type = Column(String(50), default="canvas", nullable=False)  # canvas, note, mixed
    canvas_data = Column(JSONB)  # TLDraw canvas state (JSONB for better performance)
    note_content = Column(Text)  # Markdown content
    
    # Metadata
    thumbnail_url = Column(String(512))
    is_starred = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # Soft delete
    deleted_at = Column(DateTime(timezone=True))
    view_count = Column(Integer, default=0)
    export_count = Column(Integer, default=0)  # Track number of exports
    collaborator_count = Column(Integer, default=1)  # Track number of collaborators (owner + shared users)
    comment_count = Column(Integer, default=0)  # Track number of comments
    last_edited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    tags = Column(JSON, default=[])  # Searchable tags
    size_bytes = Column(BigInteger, default=0)  # Track file size in bytes

    # Version control
    current_version = Column(Integer, default=1)
    version_count = Column(Integer, default=1)  # Track total number of versions

    # Version retention policy
    retention_policy = Column(String(20), default="keep_all", nullable=False)  # keep_all, keep_last_n, keep_duration
    retention_count = Column(Integer)  # For keep_last_n: number of versions to keep
    retention_days = Column(Integer)  # For keep_duration: number of days to keep versions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))  # Last activity (view, edit, comment)
    last_auto_versioned_at = Column(DateTime(timezone=True))  # Last time an auto-version was created
    
    # Relationships
    owner = relationship("User", back_populates="files", foreign_keys=[owner_id])
    team = relationship("Team", back_populates="files")
    folder = relationship("Folder", back_populates="files")
    versions = relationship("Version", back_populates="file", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="file", cascade="all, delete-orphan")
    shares = relationship("Share", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_files_owner', 'owner_id'),
        Index('idx_files_team', 'team_id'),
        Index('idx_files_folder', 'folder_id'),
        Index('idx_files_deleted', 'is_deleted'),
        Index('idx_files_title', 'title'),
        Index('idx_files_last_activity', 'last_activity'),
        Index('idx_files_last_edited_by', 'last_edited_by'),
        Index('idx_files_retention_policy', 'retention_policy'),
    )


class Version(Base):
    """Version history table."""
    __tablename__ = "versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Version content
    canvas_data = Column(JSONB)  # JSONB for better performance
    note_content = Column(Text)

    # Compression fields
    is_compressed = Column(Boolean, default=False, nullable=False)  # Whether content is gzipped
    compressed_canvas_data = Column(Text)  # Base64-encoded gzipped canvas_data
    compressed_note_content = Column(Text)  # Base64-encoded gzipped note_content
    original_size = Column(Integer)  # Size before compression (bytes)
    compressed_size = Column(Integer)  # Size after compression (bytes)
    compression_ratio = Column(Float)  # compressed_size / original_size
    compressed_at = Column(DateTime(timezone=True))  # When compression was applied

    # Version metadata
    description = Column(String(500))
    label = Column(String(100))
    thumbnail_url = Column(String(512))
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    file = relationship("File", back_populates="versions")

    __table_args__ = (
        Index('idx_versions_file', 'file_id'),
        Index('idx_versions_number', 'file_id', 'version_number'),
        Index('idx_versions_compressed', 'is_compressed'),
        Index('idx_versions_created', 'created_at'),
    )


class Comment(Base):
    """Comments table."""
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("comments.id", ondelete="CASCADE"))
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Comment position (for canvas comments)
    position_x = Column(Float)
    position_y = Column(Float)
    element_id = Column(String(255))  # TLDraw element ID
    
    # Comment metadata
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    is_private = Column(Boolean, default=False)  # Private comments visible only to team members
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    file = relationship("File", back_populates="comments")
    user = relationship("User", back_populates="comments", foreign_keys=[user_id])
    parent = relationship("Comment", remote_side=[id], backref="replies")
    mentions = relationship("Mention", back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_comments_file', 'file_id'),
        Index('idx_comments_user', 'user_id'),
        Index('idx_comments_parent', 'parent_id'),
    )


class Mention(Base):
    """Mentions table (@username in comments)."""
    __tablename__ = "mentions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    comment_id = Column(String(36), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Notification status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    comment = relationship("Comment", back_populates="mentions")

    __table_args__ = (
        Index('idx_mentions_comment', 'comment_id'),
        Index('idx_mentions_user', 'user_id'),
        Index('idx_mentions_unread', 'user_id', 'is_read'),
    )


class CommentReaction(Base):
    """Comment reactions table (emoji reactions)."""
    __tablename__ = "comment_reactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    comment_id = Column(String(36), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Reaction emoji (Unicode emoji or shortcode)
    emoji = Column(String(10), nullable=False)  # e.g., "👍", "❤️", "😄"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    comment = relationship("Comment", backref="reactions")

    __table_args__ = (
        Index('idx_comment_reactions_comment', 'comment_id'),
        Index('idx_comment_reactions_user', 'user_id'),
        Index('idx_comment_reactions_emoji', 'comment_id', 'emoji'),
        # Ensure one user can only have one reaction of each type per comment
        Index('idx_comment_reactions_unique', 'comment_id', 'user_id', 'emoji', unique=True),
    )


class Share(Base):
    """Share links table."""
    __tablename__ = "shares"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    
    # Share settings
    token = Column(String(255), unique=True, nullable=False, index=True)
    permission = Column(String(20), default="view", nullable=False)  # view, edit
    is_public = Column(Boolean, default=True)
    password_hash = Column(String(255))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    
    # Analytics
    view_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    file = relationship("File", back_populates="shares")

    __table_args__ = (
        Index('idx_shares_file', 'file_id'),
        Index('idx_shares_token', 'token'),
    )


class GitConnection(Base):
    """Git repository connections table."""
    __tablename__ = "git_connections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Git provider
    provider = Column(String(50), nullable=False)  # github, gitlab, bitbucket, azure
    repository_url = Column(String(512), nullable=False)
    repository_name = Column(String(255))
    branch = Column(String(255), default="main")
    
    # Authentication
    access_token = Column(String(512))  # Encrypted
    refresh_token = Column(String(512))  # Encrypted
    
    # Sync settings
    auto_sync = Column(Boolean, default=False)
    sync_frequency = Column(String(20), default="manual")  # manual, realtime, hourly, daily
    file_path = Column(String(512))  # Path in repo to save diagrams
    
    # Status
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(50))  # success, failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="git_connections")

    __table_args__ = (
        Index('idx_git_connections_user', 'user_id'),
        Index('idx_git_connections_provider', 'provider'),
    )


class AuditLog(Base):
    """Audit log table for compliance."""
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Action details
    action = Column(String(100), nullable=False)  # login, create_file, delete_file, etc.
    resource_type = Column(String(50))  # file, user, team, etc.
    resource_id = Column(String(36))
    
    # Request details
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(512))
    
    # Additional metadata
    extra_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_created', 'created_at'),
        Index('idx_audit_log_resource', 'resource_type', 'resource_id'),
    )


class ApiKey(Base):
    """API keys table."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key details
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10))  # First few chars for identification
    
    # Permissions
    scopes = Column(JSON, default=[])  # List of allowed scopes
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index('idx_api_keys_user', 'user_id'),
        Index('idx_api_keys_hash', 'key_hash'),
    )


class UsageMetric(Base):
    """Usage metrics table for analytics."""
    __tablename__ = "usage_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Metric details
    metric_type = Column(String(50), nullable=False)  # diagram_created, ai_generation, export, etc.
    metric_value = Column(Float, default=1.0)
    
    # Additional metadata
    extra_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_metrics")

    __table_args__ = (
        Index('idx_usage_metrics_user', 'user_id'),
        Index('idx_usage_metrics_type', 'metric_type'),
        Index('idx_usage_metrics_created', 'created_at'),
        Index('idx_usage_metrics_user_type', 'user_id', 'metric_type'),
    )


class RefreshToken(Base):
    """Refresh tokens table for token rotation tracking."""
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID (jti claim)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True))
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_refresh_tokens_user', 'user_id'),
        Index('idx_refresh_tokens_jti', 'token_jti'),
        Index('idx_refresh_tokens_expires', 'expires_at'),
    )


class PasswordResetToken(Base):
    """Password reset tokens table."""
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True))
    
    # Expiration (1 hour from creation)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_password_reset_tokens_user', 'user_id'),
        Index('idx_password_reset_tokens_token', 'token'),
        Index('idx_password_reset_tokens_expires', 'expires_at'),
    )


class EmailVerificationToken(Base):
    """Email verification tokens table."""
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True))
    
    # Expiration (24 hours from creation)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_email_verification_tokens_user', 'user_id'),
        Index('idx_email_verification_tokens_token', 'token'),
        Index('idx_email_verification_tokens_expires', 'expires_at'),
    )


class OAuthApp(Base):
    """OAuth 2.0 applications table (third-party apps)."""
    __tablename__ = "oauth_apps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # App details
    client_id = Column(String(255), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)  # Hashed with bcrypt
    name = Column(String(255), nullable=False)
    description = Column(Text)
    logo_url = Column(String(512))
    homepage_url = Column(String(512))
    
    # Redirect URIs (comma-separated or JSON array)
    redirect_uris = Column(JSON, nullable=False)  # List of allowed redirect URIs
    
    # Permissions
    allowed_scopes = Column(JSON, default=["read"])  # List of scopes: read, write, admin
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    authorization_codes = relationship("OAuthAuthorizationCode", back_populates="app", cascade="all, delete-orphan")
    access_tokens = relationship("OAuthAccessToken", back_populates="app", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_oauth_apps_user', 'user_id'),
        Index('idx_oauth_apps_client_id', 'client_id'),
    )


class OAuthAuthorizationCode(Base):
    """OAuth 2.0 authorization codes table."""
    __tablename__ = "oauth_authorization_codes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    app_id = Column(String(36), ForeignKey("oauth_apps.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Code details
    code = Column(String(255), unique=True, nullable=False, index=True)
    
    # Authorization details
    redirect_uri = Column(String(512), nullable=False)
    scopes = Column(JSON, nullable=False)  # List of granted scopes
    
    # PKCE (Proof Key for Code Exchange) support
    code_challenge = Column(String(255))
    code_challenge_method = Column(String(10))  # S256 or plain
    
    # Status
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True))
    
    # Expiration (10 minutes from creation)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    app = relationship("OAuthApp", back_populates="authorization_codes")
    
    __table_args__ = (
        Index('idx_oauth_codes_app', 'app_id'),
        Index('idx_oauth_codes_user', 'user_id'),
        Index('idx_oauth_codes_code', 'code'),
        Index('idx_oauth_codes_expires', 'expires_at'),
    )


class OAuthAccessToken(Base):
    """OAuth 2.0 access tokens table."""
    __tablename__ = "oauth_access_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    app_id = Column(String(36), ForeignKey("oauth_apps.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    refresh_token_jti = Column(String(255), unique=True, index=True)  # Refresh token JWT ID
    
    # Permissions
    scopes = Column(JSON, nullable=False)  # List of granted scopes
    
    # Status
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_token_expires_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    app = relationship("OAuthApp", back_populates="access_tokens")
    
    __table_args__ = (
        Index('idx_oauth_tokens_app', 'app_id'),
        Index('idx_oauth_tokens_user', 'user_id'),
        Index('idx_oauth_tokens_jti', 'token_jti'),
        Index('idx_oauth_tokens_refresh_jti', 'refresh_token_jti'),
        Index('idx_oauth_tokens_expires', 'expires_at'),
    )


class UserConsent(Base):
    """User consent tracking for GDPR compliance."""
    __tablename__ = "user_consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Consent details
    consent_type = Column(String(100), nullable=False)  # marketing, analytics, cookies, data_processing, etc.
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_version = Column(String(20))  # Version of terms/privacy policy

    # Consent context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(512))
    consent_method = Column(String(50))  # explicit, implicit, opt_in, opt_out

    # Additional metadata
    extra_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    withdrawn_at = Column(DateTime(timezone=True))  # When consent was withdrawn

    __table_args__ = (
        Index('idx_user_consents_user', 'user_id'),
        Index('idx_user_consents_type', 'consent_type'),
        Index('idx_user_consents_created', 'created_at'),
    )


class DataProcessingActivity(Base):
    """Data processing activities record for GDPR Article 30 compliance."""
    __tablename__ = "data_processing_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Activity details
    activity_name = Column(String(255), nullable=False)
    activity_description = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)  # Purpose of processing
    legal_basis = Column(String(100), nullable=False)  # consent, contract, legal_obligation, etc.

    # Data categories
    data_categories = Column(JSON, nullable=False)  # List of data categories processed
    data_subjects = Column(JSON, nullable=False)  # Categories of data subjects (users, customers, etc.)

    # Recipients
    recipients = Column(JSON)  # Who receives the data
    third_country_transfers = Column(Boolean, default=False)  # Cross-border transfers
    third_countries = Column(JSON)  # Countries data is transferred to
    safeguards = Column(Text)  # Safeguards for third country transfers

    # Retention
    retention_period = Column(String(255))  # How long data is kept

    # Security measures
    security_measures = Column(Text)

    # DPO info
    data_controller = Column(String(255))
    data_protection_officer = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_data_processing_activities_active', 'is_active'),
        Index('idx_data_processing_activities_legal_basis', 'legal_basis'),
    )


class DataBreachLog(Base):
    """Data breach notification log for GDPR Article 33/34 compliance."""
    __tablename__ = "data_breach_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Breach details
    breach_type = Column(String(100), nullable=False)  # unauthorized_access, data_loss, ransomware, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)

    # Affected data
    affected_users_count = Column(Integer, default=0)
    affected_data_categories = Column(JSON)  # Categories of data affected

    # Detection and response
    detected_at = Column(DateTime(timezone=True), nullable=False)
    contained_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))

    # Notifications
    authority_notified = Column(Boolean, default=False)  # DPA notification within 72 hours
    authority_notified_at = Column(DateTime(timezone=True))
    users_notified = Column(Boolean, default=False)  # User notification if high risk
    users_notified_at = Column(DateTime(timezone=True))

    # Risk assessment
    likely_consequences = Column(Text)
    measures_taken = Column(Text)
    measures_proposed = Column(Text)

    # Responsible parties
    reported_by = Column(String(255))
    dpo_notified = Column(Boolean, default=False)
    dpo_notified_at = Column(DateTime(timezone=True))

    # Status
    status = Column(String(50), default="open")  # open, investigating, contained, resolved, closed

    # Additional metadata
    extra_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_data_breach_logs_severity', 'severity'),
        Index('idx_data_breach_logs_status', 'status'),
        Index('idx_data_breach_logs_detected', 'detected_at'),
    )


class DataDeletionRequest(Base):
    """Track user data deletion requests (right to be forgotten)."""
    __tablename__ = "data_deletion_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    user_email = Column(String(255), nullable=False)  # Store email in case user is deleted

    # Request details
    request_reason = Column(Text)
    verification_token = Column(String(255), unique=True)
    verified_at = Column(DateTime(timezone=True))

    # Processing status
    status = Column(String(50), default="pending", nullable=False)  # pending, verified, processing, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Deletion summary
    tables_processed = Column(JSON)  # List of tables from which data was deleted
    records_deleted = Column(Integer, default=0)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_data_deletion_requests_user', 'user_id'),
        Index('idx_data_deletion_requests_email', 'user_email'),
        Index('idx_data_deletion_requests_status', 'status'),
        Index('idx_data_deletion_requests_token', 'verification_token'),
    )


class PushSubscription(Base):
    """Push notification subscriptions for PWA."""
    __tablename__ = "push_subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Subscription details (from PushSubscription API)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(255), nullable=False)  # Public key for encryption
    auth = Column(String(255), nullable=False)  # Authentication secret

    # Device/browser info
    user_agent = Column(Text)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_push_subscriptions_user', 'user_id'),
        Index('idx_push_subscriptions_endpoint', 'endpoint', unique=True, postgresql_using='hash'),
        Index('idx_push_subscriptions_active', 'user_id', 'is_active'),
    )


class SCIMToken(Base):
    """SCIM API tokens for provisioning."""
    __tablename__ = "scim_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token_hash = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    scopes = Column(JSON, default=["read", "write"])
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_scim_tokens_hash', 'token_hash'),
        Index('idx_scim_tokens_active', 'is_active'),
    )
