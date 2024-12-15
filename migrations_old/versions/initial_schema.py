"""Initial database schema

Revision ID: initial_schema
Revises: None
Create Date: 2024-01-02 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create User table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('employee_number', sa.String(32), unique=True),
        sa.Column('name', sa.String(128)),
        sa.Column('email', sa.String(128)),
        sa.Column('vzid', sa.String(32), unique=True),
        sa.Column('password_hash', sa.String(256)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('avatar_data', sa.LargeBinary),
        sa.Column('avatar_mimetype', sa.String(32)),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Role table with RBAC support
    op.create_table('role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), unique=True, nullable=False),
        sa.Column('description', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['role.id'])
    )

    # Create Action table
    op.create_table('action',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('method', sa.String(10), nullable=True),
        sa.Column('description', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'method', name='_action_method_uc')
    )

    # Create Permission table
    op.create_table('permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create NavigationCategory table
    op.create_table('navigation_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), unique=True, nullable=False),
        sa.Column('icon', sa.String(32)),
        sa.Column('description', sa.String(256)),
        sa.Column('weight', sa.Integer(), default=0),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_by', sa.String(64)),
        sa.Column('updated_at', sa.DateTime(), onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )

    # Create association tables
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    op.create_table('permission_actions',
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id']),
        sa.ForeignKeyConstraint(['action_id'], ['action.id']),
        sa.PrimaryKeyConstraint('permission_id', 'action_id')
    )

    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id']),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # Create RoutePermission table
    op.create_table('route_permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(256), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route', 'permission_id', name='_route_permission_uc')
    )

    # Create UserPreference table
    op.create_table('user_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(64), nullable=False),
        sa.Column('value', sa.String(256)),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'key', name='_user_key_uc')
    )

    # Create UserActivity table
    op.create_table('user_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('username', sa.String(64)),
        sa.Column('activity', sa.String(512), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create PageVisit table
    op.create_table('page_visit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(256), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('username', sa.String(64)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(256)),
        sa.Column('timestamp', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('page_visit')
    op.drop_table('user_activity')
    op.drop_table('user_preference')
    op.drop_table('route_permission')
    op.drop_table('role_permissions')
    op.drop_table('permission_actions')
    op.drop_table('user_roles')
    op.drop_table('navigation_category')
    op.drop_table('permission')
    op.drop_table('action')
    op.drop_table('role')
    op.drop_table('user')
