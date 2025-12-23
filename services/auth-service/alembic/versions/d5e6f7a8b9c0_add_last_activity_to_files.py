"""add_last_activity_to_files

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2025-12-23 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    """Add last_activity column to files table for tracking last activity timestamp."""
    # Add last_activity column with default value of current timestamp
    op.add_column('files', sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True))
    
    # Set initial value to updated_at for existing records
    op.execute("UPDATE files SET last_activity = updated_at WHERE last_activity IS NULL")
    
    # Create index for sorting by last_activity
    op.create_index('idx_files_last_activity', 'files', ['last_activity'])


def downgrade():
    """Remove last_activity column from files table."""
    op.drop_index('idx_files_last_activity', table_name='files')
    op.drop_column('files', 'last_activity')
