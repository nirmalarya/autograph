"""add_user_preferences_column

Revision ID: d46e4fee5009
Revises: 6024161a252f
Create Date: 2025-12-22 17:19:02.799803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd46e4fee5009'
down_revision = '6024161a252f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add preferences column to users table (JSONB for flexible user preferences)
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))
    
    # Add default preferences for existing users
    op.execute("UPDATE users SET preferences = '{}' WHERE preferences IS NULL")


def downgrade() -> None:
    # Remove preferences column
    op.drop_column('users', 'preferences')
