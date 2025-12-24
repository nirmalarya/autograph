"""Add OAuth 2.0 tables

Revision ID: d22e681a1d5e
Revises: 9e37e829dc92
Create Date: 2025-12-23 21:59:20.992614

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = 'd22e681a1d5e'
down_revision = '9e37e829dc92'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create oauth_apps table
    op.create_table(
        'oauth_apps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('client_id', sa.String(255), unique=True, nullable=False),
        sa.Column('client_secret_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('logo_url', sa.String(512)),
        sa.Column('homepage_url', sa.String(512)),
        sa.Column('redirect_uris', JSON, nullable=False),
        sa.Column('allowed_scopes', JSON, server_default='["read"]'),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('idx_oauth_apps_user', 'oauth_apps', ['user_id'])
    op.create_index('idx_oauth_apps_client_id', 'oauth_apps', ['client_id'])
    
    # Create oauth_authorization_codes table
    op.create_table(
        'oauth_authorization_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('app_id', sa.String(36), sa.ForeignKey('oauth_apps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(255), unique=True, nullable=False),
        sa.Column('redirect_uri', sa.String(512), nullable=False),
        sa.Column('scopes', JSON, nullable=False),
        sa.Column('code_challenge', sa.String(255)),
        sa.Column('code_challenge_method', sa.String(10)),
        sa.Column('is_used', sa.Boolean, default=False, nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_oauth_codes_app', 'oauth_authorization_codes', ['app_id'])
    op.create_index('idx_oauth_codes_user', 'oauth_authorization_codes', ['user_id'])
    op.create_index('idx_oauth_codes_code', 'oauth_authorization_codes', ['code'])
    op.create_index('idx_oauth_codes_expires', 'oauth_authorization_codes', ['expires_at'])
    
    # Create oauth_access_tokens table
    op.create_table(
        'oauth_access_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('app_id', sa.String(36), sa.ForeignKey('oauth_apps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_jti', sa.String(255), unique=True, nullable=False),
        sa.Column('refresh_token_jti', sa.String(255), unique=True),
        sa.Column('scopes', JSON, nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False, nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_token_expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_oauth_tokens_app', 'oauth_access_tokens', ['app_id'])
    op.create_index('idx_oauth_tokens_user', 'oauth_access_tokens', ['user_id'])
    op.create_index('idx_oauth_tokens_jti', 'oauth_access_tokens', ['token_jti'])
    op.create_index('idx_oauth_tokens_refresh_jti', 'oauth_access_tokens', ['refresh_token_jti'])
    op.create_index('idx_oauth_tokens_expires', 'oauth_access_tokens', ['expires_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('oauth_access_tokens')
    op.drop_table('oauth_authorization_codes')
    op.drop_table('oauth_apps')
