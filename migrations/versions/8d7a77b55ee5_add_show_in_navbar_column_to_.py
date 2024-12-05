"""Add show_in_navbar column to PageRouteMapping

Revision ID: 8d7a77b55ee5
Revises: dispatch_route_mappings
Create Date: 2024-12-05 12:49:19.366852

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d7a77b55ee5'
down_revision = 'dispatch_route_mappings'
branch_labels = None
depends_on = None


def upgrade():
    # Create new table
    op.create_table('_page_route_mapping_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_name', sa.String(length=128), nullable=False),
        sa.Column('route', sa.String(length=256), nullable=False),
        sa.Column('icon', sa.String(length=64), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('show_in_navbar', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['navigation_category.id'], name='fk_page_route_category'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route')
    )

    # Copy data
    op.execute('''
        INSERT INTO _page_route_mapping_new (
            id, page_name, route, icon, weight, created_at, updated_at, category_id
        )
        SELECT id, page_name, route, icon, weight, created_at, updated_at, category_id
        FROM page_route_mapping
    ''')

    # Drop old table
    op.drop_table('page_route_mapping')

    # Rename new table to old name
    op.rename_table('_page_route_mapping_new', 'page_route_mapping')


def downgrade():
    # Create table without show_in_navbar column
    op.create_table('_page_route_mapping_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('page_name', sa.String(length=128), nullable=False),
        sa.Column('route', sa.String(length=256), nullable=False),
        sa.Column('icon', sa.String(length=64), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['navigation_category.id'], name='fk_page_route_category'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route')
    )

    # Copy data
    op.execute('''
        INSERT INTO _page_route_mapping_old (
            id, page_name, route, icon, weight, created_at, updated_at, category_id
        )
        SELECT id, page_name, route, icon, weight, created_at, updated_at, category_id
        FROM page_route_mapping
    ''')

    # Drop new table
    op.drop_table('page_route_mapping')

    # Rename old table to original name
    op.rename_table('_page_route_mapping_old', 'page_route_mapping')
