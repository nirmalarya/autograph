"""add_last_edited_by_to_files

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-23 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    """Add last_edited_by column to files table for tracking who last modified the diagram."""
    # Add last_edited_by column
    op.add_column('files', sa.Column('last_edited_by', sa.String(36), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_files_last_edited_by',
        'files', 'users',
        ['last_edited_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for performance
    op.create_index('idx_files_last_edited_by', 'files', ['last_edited_by'])


def downgrade():
    """Remove last_edited_by column from files table."""
    op.drop_index('idx_files_last_edited_by', table_name='files')
    op.drop_constraint('fk_files_last_edited_by', 'files', type_='foreignkey')
    op.drop_column('files', 'last_edited_by')
