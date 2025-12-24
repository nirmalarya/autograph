"""add azure devops tables

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2025-12-24 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'l7m8n9o0p1q2'
down_revision = 'k6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade():
    # Create azure_devops_connections table
    op.create_table(
        'azure_devops_connections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization', sa.String(255), nullable=False),  # e.g., "bayer"
        sa.Column('project', sa.String(255), nullable=False),  # e.g., "PHCom"
        sa.Column('personal_access_token', sa.String(512), nullable=False),  # PAT for authentication
        sa.Column('area_path', sa.String(512), nullable=True),  # e.g., "PHCom/IDP"
        sa.Column('iteration_path', sa.String(512), nullable=True),  # e.g., "Sprint 23"
        sa.Column('auto_sync', sa.Boolean(), default=False),
        sa.Column('sync_frequency', sa.String(20), default='manual'),  # manual, hourly, daily
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    
    # Create azure_devops_work_items table
    op.create_table(
        'azure_devops_work_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('connection_id', sa.String(36), sa.ForeignKey('azure_devops_connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('work_item_id', sa.Integer(), nullable=False),  # Azure DevOps work item ID
        sa.Column('work_item_type', sa.String(50), nullable=False),  # User Story, Task, Bug, etc.
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),  # New, Active, Resolved, Closed
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('area_path', sa.String(512), nullable=True),
        sa.Column('iteration_path', sa.String(512), nullable=True),
        sa.Column('diagram_id', sa.String(36), sa.ForeignKey('files.id', ondelete='SET NULL'), nullable=True),  # Link to generated diagram
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.UniqueConstraint('connection_id', 'work_item_id', name='unique_work_item_per_connection')
    )
    
    # Create index for faster lookups
    op.create_index('idx_azure_devops_connections_user_id', 'azure_devops_connections', ['user_id'])
    op.create_index('idx_azure_devops_work_items_connection_id', 'azure_devops_work_items', ['connection_id'])
    op.create_index('idx_azure_devops_work_items_diagram_id', 'azure_devops_work_items', ['diagram_id'])
    op.create_index('idx_azure_devops_work_items_work_item_id', 'azure_devops_work_items', ['work_item_id'])


def downgrade():
    op.drop_index('idx_azure_devops_work_items_work_item_id')
    op.drop_index('idx_azure_devops_work_items_diagram_id')
    op.drop_index('idx_azure_devops_work_items_connection_id')
    op.drop_index('idx_azure_devops_connections_user_id')
    op.drop_table('azure_devops_work_items')
    op.drop_table('azure_devops_connections')
