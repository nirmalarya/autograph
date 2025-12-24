"""Add team_members table for team management

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2025-12-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='viewer'),
        sa.Column('invited_by', sa.String(length=36), nullable=True),
        sa.Column('invitation_status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('invitation_token', sa.String(length=255), nullable=True),
        sa.Column('invitation_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_team_members_team', 'team_members', ['team_id'])
    op.create_index('idx_team_members_user', 'team_members', ['user_id'])
    op.create_index('idx_team_members_invitation_token', 'team_members', ['invitation_token'])
    op.create_index('idx_team_members_unique', 'team_members', ['team_id', 'user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_team_members_unique', table_name='team_members')
    op.drop_index('idx_team_members_invitation_token', table_name='team_members')
    op.drop_index('idx_team_members_user', table_name='team_members')
    op.drop_index('idx_team_members_team', table_name='team_members')
    op.drop_table('team_members')
