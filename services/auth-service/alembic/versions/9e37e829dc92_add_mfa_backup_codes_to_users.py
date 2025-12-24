"""add_mfa_backup_codes_to_users

Revision ID: 9e37e829dc92
Revises: i4j5k6l7m8n9
Create Date: 2025-12-23 21:35:30.468999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e37e829dc92'
down_revision = 'i4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add mfa_backup_codes JSON column to users table
    op.add_column('users', sa.Column('mfa_backup_codes', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove mfa_backup_codes column
    op.drop_column('users', 'mfa_backup_codes')
