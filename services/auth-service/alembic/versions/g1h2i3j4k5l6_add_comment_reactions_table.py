"""add_comment_reactions_table

Revision ID: g1h2i3j4k5l6
Revises: c3d4e5f6a7b8
Create Date: 2025-12-23 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g1h2i3j4k5l6'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    """Create comment_reactions table for emoji reactions on comments."""
    op.create_table(
        'comment_reactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('comment_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_comment_reactions_comment', 'comment_reactions', ['comment_id'])
    op.create_index('idx_comment_reactions_user', 'comment_reactions', ['user_id'])
    op.create_index('idx_comment_reactions_emoji', 'comment_reactions', ['comment_id', 'emoji'])
    op.create_index('idx_comment_reactions_unique', 'comment_reactions', ['comment_id', 'user_id', 'emoji'], unique=True)


def downgrade():
    """Drop comment_reactions table."""
    op.drop_index('idx_comment_reactions_unique', table_name='comment_reactions')
    op.drop_index('idx_comment_reactions_emoji', table_name='comment_reactions')
    op.drop_index('idx_comment_reactions_user', table_name='comment_reactions')
    op.drop_index('idx_comment_reactions_comment', table_name='comment_reactions')
    op.drop_table('comment_reactions')
