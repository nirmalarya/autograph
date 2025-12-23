"""add password reset tokens table

Revision ID: f9a4b3c2d1e5
Revises: e8f3a9b2c1d4
Create Date: 2025-12-23 06:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f9a4b3c2d1e5'
down_revision = 'e8f3a9b2c1d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_password_reset_tokens_user', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)
    op.create_index('idx_password_reset_tokens_expires', 'password_reset_tokens', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_password_reset_tokens_expires', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('idx_password_reset_tokens_user', table_name='password_reset_tokens')
    
    # Drop table
    op.drop_table('password_reset_tokens')
