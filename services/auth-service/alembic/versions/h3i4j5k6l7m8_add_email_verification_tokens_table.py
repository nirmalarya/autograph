"""add email verification tokens table

Revision ID: h3i4j5k6l7m8
Revises: ef8786740bda
Create Date: 2025-12-24 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'h3i4j5k6l7m8'
down_revision = 'ef8786740bda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_verification_tokens table
    op.create_table('email_verification_tokens',
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
    op.create_index('idx_email_verification_tokens_user', 'email_verification_tokens', ['user_id'], unique=False)
    op.create_index('idx_email_verification_tokens_token', 'email_verification_tokens', ['token'], unique=True)
    op.create_index('idx_email_verification_tokens_expires', 'email_verification_tokens', ['expires_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_email_verification_tokens_expires', table_name='email_verification_tokens')
    op.drop_index('idx_email_verification_tokens_token', table_name='email_verification_tokens')
    op.drop_index('idx_email_verification_tokens_user', table_name='email_verification_tokens')
    
    # Drop table
    op.drop_table('email_verification_tokens')
