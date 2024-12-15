"""Add soft delete to reports models

Revision ID: add_reports_soft_delete
Revises: add_awsmon_user_tracking
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reports_soft_delete'
down_revision = 'add_awsmon_user_tracking'
branch_labels = None
depends_on = None

def upgrade():
    # Add deleted_at column to database_connection table
    op.add_column('database_connection', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add deleted_at column to report_view table
    op.add_column('report_view', sa.Column('deleted_at', sa.DateTime(), nullable=True))

def downgrade():
    # Remove deleted_at column from database_connection table
    op.drop_column('database_connection', 'deleted_at')
    
    # Remove deleted_at column from report_view table
    op.drop_column('report_view', 'deleted_at')
