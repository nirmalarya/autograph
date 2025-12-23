"""add_export_count_to_files

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-23 12:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    """Add export_count column to files table for tracking number of exports."""
    # Add export_count column with default value of 0
    op.add_column('files', sa.Column('export_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    """Remove export_count column from files table."""
    op.drop_column('files', 'export_count')
