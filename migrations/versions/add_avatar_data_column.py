"""Add avatar data column to user table

Revision ID: add_avatar_data_column
Revises: add_monitoring_tables
Create Date: 2024-12-12 18:51:36.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_avatar_data_column'
down_revision = 'add_monitoring_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Add avatar_data column to store binary image data
    op.add_column('user', sa.Column('avatar_data', sa.LargeBinary(), nullable=True))
    op.add_column('user', sa.Column('avatar_mimetype', sa.String(length=32), nullable=True))

def downgrade():
    op.drop_column('user', 'avatar_data')
    op.drop_column('user', 'avatar_mimetype')
