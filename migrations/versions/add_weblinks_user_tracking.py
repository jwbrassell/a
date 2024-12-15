"""Add user tracking and soft delete to weblinks models

Revision ID: add_weblinks_user_tracking
Revises: add_reports_soft_delete
Create Date: 2024-01-10 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_weblinks_user_tracking'
down_revision = 'add_reports_soft_delete'
branch_labels = None
depends_on = None

def upgrade():
    # Temporary tables to store username to user_id mappings
    op.create_table(
        'temp_weblink_users',
        sa.Column('username', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=True)
    )
    op.create_table(
        'temp_category_users',
        sa.Column('username', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=True)
    )
    op.create_table(
        'temp_tag_users',
        sa.Column('username', sa.String(100), primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=True)
    )

    # Add new columns to weblinks table
    op.add_column('weblinks', sa.Column('updated_by', sa.Integer, sa.ForeignKey('user.id')))
    op.add_column('weblinks', sa.Column('deleted_at', sa.DateTime, nullable=True))
    op.add_column('weblinks', sa.Column('temp_created_by', sa.Integer, sa.ForeignKey('user.id')))

    # Add new columns to weblink_categories table
    op.add_column('weblink_categories', sa.Column('updated_by', sa.Integer, sa.ForeignKey('user.id')))
    op.add_column('weblink_categories', sa.Column('updated_at', sa.DateTime, default=datetime.utcnow))
    op.add_column('weblink_categories', sa.Column('deleted_at', sa.DateTime, nullable=True))
    op.add_column('weblink_categories', sa.Column('temp_created_by', sa.Integer, sa.ForeignKey('user.id')))

    # Add new columns to weblink_tags table
    op.add_column('weblink_tags', sa.Column('updated_by', sa.Integer, sa.ForeignKey('user.id')))
    op.add_column('weblink_tags', sa.Column('updated_at', sa.DateTime, default=datetime.utcnow))
    op.add_column('weblink_tags', sa.Column('deleted_at', sa.DateTime, nullable=True))
    op.add_column('weblink_tags', sa.Column('temp_created_by', sa.Integer, sa.ForeignKey('user.id')))

    # Create indexes for better query performance
    op.create_index('ix_weblinks_deleted_at', 'weblinks', ['deleted_at'])
    op.create_index('ix_weblink_categories_deleted_at', 'weblink_categories', ['deleted_at'])
    op.create_index('ix_weblink_tags_deleted_at', 'weblink_tags', ['deleted_at'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_weblinks_deleted_at')
    op.drop_index('ix_weblink_categories_deleted_at')
    op.drop_index('ix_weblink_tags_deleted_at')

    # Remove columns from weblinks table
    op.drop_column('weblinks', 'updated_by')
    op.drop_column('weblinks', 'deleted_at')
    op.drop_column('weblinks', 'temp_created_by')

    # Remove columns from weblink_categories table
    op.drop_column('weblink_categories', 'updated_by')
    op.drop_column('weblink_categories', 'updated_at')
    op.drop_column('weblink_categories', 'deleted_at')
    op.drop_column('weblink_categories', 'temp_created_by')

    # Remove columns from weblink_tags table
    op.drop_column('weblink_tags', 'updated_by')
    op.drop_column('weblink_tags', 'updated_at')
    op.drop_column('weblink_tags', 'deleted_at')
    op.drop_column('weblink_tags', 'temp_created_by')

    # Drop temporary tables
    op.drop_table('temp_weblink_users')
    op.drop_table('temp_category_users')
    op.drop_table('temp_tag_users')
