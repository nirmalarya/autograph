"""add tags to files

Revision ID: j5k6l7m8n9o0
Revises: 324f3b6f5871
Create Date: 2025-12-24 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n9o0'
down_revision = '324f3b6f5871'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tags column to files table (using JSON type)
    op.add_column('files', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'))


def downgrade() -> None:
    # Drop tags column
    op.drop_column('files', 'tags')
