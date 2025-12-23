"""convert_canvas_data_to_jsonb

Revision ID: 07d62c34fdd3
Revises: d46e4fee5009
Create Date: 2025-12-22 20:21:38.200814

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '07d62c34fdd3'
down_revision = 'd46e4fee5009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert canvas_data columns from JSON to JSONB for better performance."""
    # Convert files.canvas_data from JSON to JSONB
    # Using USING clause to handle the type conversion
    op.execute("""
        ALTER TABLE files 
        ALTER COLUMN canvas_data TYPE JSONB USING canvas_data::jsonb
    """)
    
    # Convert versions.canvas_data from JSON to JSONB
    op.execute("""
        ALTER TABLE versions 
        ALTER COLUMN canvas_data TYPE JSONB USING canvas_data::jsonb
    """)
    
    # Add GIN index on files.canvas_data for efficient JSONB queries
    # GIN (Generalized Inverted Index) is ideal for JSONB containment queries
    op.create_index(
        'idx_files_canvas_data_gin',
        'files',
        ['canvas_data'],
        unique=False,
        postgresql_using='gin'
    )
    
    # Add GIN index on versions.canvas_data
    op.create_index(
        'idx_versions_canvas_data_gin',
        'versions',
        ['canvas_data'],
        unique=False,
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Convert canvas_data columns back from JSONB to JSON."""
    # Drop GIN indexes first
    op.drop_index('idx_versions_canvas_data_gin', table_name='versions')
    op.drop_index('idx_files_canvas_data_gin', table_name='files')
    
    # Convert back to JSON
    op.execute("""
        ALTER TABLE versions 
        ALTER COLUMN canvas_data TYPE JSON USING canvas_data::json
    """)
    
    op.execute("""
        ALTER TABLE files 
        ALTER COLUMN canvas_data TYPE JSON USING canvas_data::json
    """)
