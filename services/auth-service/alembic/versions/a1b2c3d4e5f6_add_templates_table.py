"""add templates table

Revision ID: a1b2c3d4e5f6
Revises: f9a4b3c2d1e5
Create Date: 2025-12-23 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f9a4b3c2d1e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False, server_default='canvas'),
        sa.Column('canvas_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('note_content', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=512), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_templates_owner', 'templates', ['owner_id'])
    op.create_index('idx_templates_public', 'templates', ['is_public'])
    op.create_index('idx_templates_category', 'templates', ['category'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_templates_category', table_name='templates')
    op.drop_index('idx_templates_public', table_name='templates')
    op.drop_index('idx_templates_owner', table_name='templates')
    
    # Drop table
    op.drop_table('templates')
