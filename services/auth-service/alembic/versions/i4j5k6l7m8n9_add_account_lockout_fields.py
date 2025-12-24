"""add account lockout fields

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2025-12-24 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'i4j5k6l7m8n9'
down_revision = 'h3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account lockout fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Create index on locked_until for faster queries
    op.create_index('idx_users_locked_until', 'users', ['locked_until'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_users_locked_until', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
