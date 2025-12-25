"""add_gdpr_compliance_tables

Revision ID: gdpr_001
Revises: d22e681a1d5e
Create Date: 2024-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'gdpr_001'
down_revision = 'd22e681a1d5e'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_consents table
    op.create_table(
        'user_consents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('consent_given', sa.Boolean(), default=False, nullable=False),
        sa.Column('consent_version', sa.String(20)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(512)),
        sa.Column('consent_method', sa.String(50)),
        sa.Column('extra_data', postgresql.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True)),
    )

    op.create_index('idx_user_consents_user', 'user_consents', ['user_id'])
    op.create_index('idx_user_consents_type', 'user_consents', ['consent_type'])
    op.create_index('idx_user_consents_created', 'user_consents', ['created_at'])

    # Create data_processing_activities table
    op.create_table(
        'data_processing_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('activity_name', sa.String(255), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.String(100), nullable=False),
        sa.Column('data_categories', postgresql.JSON, nullable=False),
        sa.Column('data_subjects', postgresql.JSON, nullable=False),
        sa.Column('recipients', postgresql.JSON),
        sa.Column('third_country_transfers', sa.Boolean(), default=False),
        sa.Column('third_countries', postgresql.JSON),
        sa.Column('safeguards', sa.Text()),
        sa.Column('retention_period', sa.String(255)),
        sa.Column('security_measures', sa.Text()),
        sa.Column('data_controller', sa.String(255)),
        sa.Column('data_protection_officer', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('idx_data_processing_activities_active', 'data_processing_activities', ['is_active'])
    op.create_index('idx_data_processing_activities_legal_basis', 'data_processing_activities', ['legal_basis'])

    # Create data_breach_logs table
    op.create_table(
        'data_breach_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('breach_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_users_count', sa.Integer(), default=0),
        sa.Column('affected_data_categories', postgresql.JSON),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('contained_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('authority_notified', sa.Boolean(), default=False),
        sa.Column('authority_notified_at', sa.DateTime(timezone=True)),
        sa.Column('users_notified', sa.Boolean(), default=False),
        sa.Column('users_notified_at', sa.DateTime(timezone=True)),
        sa.Column('likely_consequences', sa.Text()),
        sa.Column('measures_taken', sa.Text()),
        sa.Column('measures_proposed', sa.Text()),
        sa.Column('reported_by', sa.String(255)),
        sa.Column('dpo_notified', sa.Boolean(), default=False),
        sa.Column('dpo_notified_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(50), default='open'),
        sa.Column('extra_data', postgresql.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('idx_data_breach_logs_severity', 'data_breach_logs', ['severity'])
    op.create_index('idx_data_breach_logs_status', 'data_breach_logs', ['status'])
    op.create_index('idx_data_breach_logs_detected', 'data_breach_logs', ['detected_at'])

    # Create data_deletion_requests table
    op.create_table(
        'data_deletion_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('request_reason', sa.Text()),
        sa.Column('verification_token', sa.String(255), unique=True),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('tables_processed', postgresql.JSON),
        sa.Column('records_deleted', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('idx_data_deletion_requests_user', 'data_deletion_requests', ['user_id'])
    op.create_index('idx_data_deletion_requests_email', 'data_deletion_requests', ['user_email'])
    op.create_index('idx_data_deletion_requests_status', 'data_deletion_requests', ['status'])
    op.create_index('idx_data_deletion_requests_token', 'data_deletion_requests', ['verification_token'])


def downgrade():
    op.drop_table('data_deletion_requests')
    op.drop_table('data_breach_logs')
    op.drop_table('data_processing_activities')
    op.drop_table('user_consents')
