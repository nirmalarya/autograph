"""Database models for Git Service."""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID string."""
    return str(uuid.uuid4())


class AzureDevOpsConnection(Base):
    """Azure DevOps connection model."""
    __tablename__ = 'azure_devops_connections'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    organization = Column(String(255), nullable=False)
    project = Column(String(255), nullable=False)
    personal_access_token = Column(String(512), nullable=False)
    area_path = Column(String(512), nullable=True)
    iteration_path = Column(String(512), nullable=True)
    auto_sync = Column(Boolean, default=False)
    sync_frequency = Column(String(20), default='manual')
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AzureDevOpsWorkItem(Base):
    """Azure DevOps work item model."""
    __tablename__ = 'azure_devops_work_items'
    __table_args__ = (
        UniqueConstraint('connection_id', 'work_item_id', name='unique_work_item_per_connection'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    connection_id = Column(String(36), ForeignKey('azure_devops_connections.id', ondelete='CASCADE'), nullable=False)
    work_item_id = Column(Integer, nullable=False)
    work_item_type = Column(String(50), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    state = Column(String(50), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    area_path = Column(String(512), nullable=True)
    iteration_path = Column(String(512), nullable=True)
    diagram_id = Column(String(36), ForeignKey('files.id', ondelete='SET NULL'), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
