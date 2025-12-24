"""add_last_auto_versioned_at_to_files

Revision ID: 324f3b6f5871
Revises: d22e681a1d5e
Create Date: 2025-12-23 22:15:25.552988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '324f3b6f5871'
down_revision = 'd22e681a1d5e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_auto_versioned_at column to files table
    op.add_column('files', sa.Column('last_auto_versioned_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove last_auto_versioned_at column from files table
    op.drop_column('files', 'last_auto_versioned_at')
