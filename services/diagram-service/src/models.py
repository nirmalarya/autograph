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

    __table_args__ = (
        Index('idx_teams_slug', 'slug'),
        Index('idx_teams_owner', 'owner_id'),
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
    original_size = Column(BigInteger)  # Size before compression (bytes)
    compressed_size = Column(BigInteger)  # Size after compression (bytes)
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
    
    # Version-specific sharing (optional - if set, share points to specific version)
    version_id = Column(String(36), ForeignKey("versions.id", ondelete="CASCADE"))
    
    # Share settings
    token = Column(String(255), unique=True, nullable=False, index=True)
    permission = Column(String(20), default="view", nullable=False)  # view, edit
    is_public = Column(Boolean, default=True)
    password_hash = Column(String(255))
    
    # User-specific sharing (for "Shared with me" feature)
    shared_with_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    
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
        Index('idx_shares_user', 'shared_with_user_id'),
        Index('idx_shares_version', 'version_id'),
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


class Template(Base):
    """Diagram template table for reusable patterns."""
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Template content (same as diagram)
    file_type = Column(String(50), default="canvas", nullable=False)  # canvas, note, mixed
    canvas_data = Column(JSONB)  # TLDraw canvas state
    note_content = Column(Text)  # Markdown content
    
    # Template metadata
    thumbnail_url = Column(String(512))
    is_public = Column(Boolean, default=False)  # Public templates visible to all users
    usage_count = Column(Integer, default=0)  # Track how many times template is used
    category = Column(String(100))  # e.g., "Architecture", "Flowchart", "ERD"
    tags = Column(JSON, default=[])  # Searchable tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("User")

    __table_args__ = (
        Index('idx_templates_owner', 'owner_id'),
        Index('idx_templates_public', 'is_public'),
        Index('idx_templates_category', 'category'),
    )


class ExportHistory(Base):
    """Export history table for tracking all exports."""
    __tablename__ = "export_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Export details
    export_format = Column(String(20), nullable=False)  # png, svg, pdf, json, md, html
    export_type = Column(String(50), default="full")  # full, selection, figure
    
    # Export settings (stored as JSON for flexibility)
    export_settings = Column(JSON, default={})  # Resolution, quality, background, etc.
    
    # File information
    file_size = Column(BigInteger)  # Size in bytes
    file_path = Column(String(1024))  # Path in storage (MinIO or S3)
    download_url = Column(String(1024))  # Temporary download URL
    
    # Status
    status = Column(String(20), default="completed", nullable=False)  # pending, completed, failed
    error_message = Column(Text)  # Error details if failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True))  # When the exported file expires (cleanup)
    
    # Relationships
    file = relationship("File")
    user = relationship("User")

    __table_args__ = (
        Index('idx_export_history_file', 'file_id'),
        Index('idx_export_history_user', 'user_id'),
        Index('idx_export_history_created', 'created_at'),
        Index('idx_export_history_format', 'export_format'),
        Index('idx_export_history_status', 'status'),
        Index('idx_export_history_expires', 'expires_at'),
    )
