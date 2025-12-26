"""Add push subscriptions table (merge)

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2, gdpr_001
Create Date: 2025-12-26 00:36:17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'm8n9o0p1q2r3'
down_revision = ('l7m8n9o0p1q2', 'gdpr_001')
branch_labels = None
depends_on = None


def upgrade():
    # Create push_subscriptions table
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.String(255), nullable=False),
        sa.Column('auth', sa.String(255), nullable=False),
        sa.Column('user_agent', sa.Text()),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
    )
    
    # Create indexes
    op.create_index('idx_push_subscriptions_user', 'push_subscriptions', ['user_id'])
    op.create_index('idx_push_subscriptions_endpoint', 'push_subscriptions', ['endpoint'], unique=True)
    op.create_index('idx_push_subscriptions_active', 'push_subscriptions', ['user_id', 'is_active'])


def downgrade():
    op.drop_index('idx_push_subscriptions_active', table_name='push_subscriptions')
    op.drop_index('idx_push_subscriptions_endpoint', table_name='push_subscriptions')
    op.drop_index('idx_push_subscriptions_user', table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
