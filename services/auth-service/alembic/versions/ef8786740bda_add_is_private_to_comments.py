"""add_is_private_to_comments

Revision ID: ef8786740bda
Revises: efba7559e83f
Create Date: 2025-12-23 18:40:35.569753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef8786740bda'
down_revision = 'efba7559e83f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_private column to comments table
    op.add_column('comments', sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_private column from comments table
    op.drop_column('comments', 'is_private')
