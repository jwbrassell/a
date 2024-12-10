"""Add badge support to navigation.

Revision ID: add_nav_badges
Revises: 5b2bffe3aff9
Create Date: 2024-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_nav_badges'
down_revision = '5b2bffe3aff9'
branch_labels = None
depends_on = None

def upgrade():
    # Add badge columns to navigation_category
    op.add_column('navigation_category',
        sa.Column('badge_text', sa.String(32), nullable=True)
    )
    op.add_column('navigation_category',
        sa.Column('badge_type', sa.String(32), nullable=True)
    )

    # Add badge columns to page_route_mapping
    op.add_column('page_route_mapping',
        sa.Column('badge_text', sa.String(32), nullable=True)
    )
    op.add_column('page_route_mapping',
        sa.Column('badge_type', sa.String(32), nullable=True)
    )

def downgrade():
    # Remove badge columns from navigation_category
    op.drop_column('navigation_category', 'badge_text')
    op.drop_column('navigation_category', 'badge_type')

    # Remove badge columns from page_route_mapping
    op.drop_column('page_route_mapping', 'badge_text')
    op.drop_column('page_route_mapping', 'badge_type')
