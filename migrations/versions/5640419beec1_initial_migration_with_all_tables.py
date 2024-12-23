"""Initial migration with all tables

Revision ID: 5640419beec1
Revises: 
Create Date: 2024-12-23 08:32:26.126776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5640419beec1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create core tables first
    op.create_table('action',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'method', name='_action_method_uc')
    )

    op.create_table('permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table('role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), unique=True, nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=64), nullable=True),
        sa.Column('ldap_groups', sa.JSON(), nullable=True),
        sa.Column('auto_sync', sa.Boolean(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), unique=True, nullable=False),
        sa.Column('employee_number', sa.String(length=32), unique=True),
        sa.Column('name', sa.String(length=128)),
        sa.Column('email', sa.String(length=128)),
        sa.Column('vzid', sa.String(length=32), unique=True),
        sa.Column('password_hash', sa.String(length=256)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('avatar_data', sa.LargeBinary()),
        sa.Column('avatar_mimetype', sa.String(length=32)),
        sa.PrimaryKeyConstraint('id')
    )

    # Create association tables
    op.create_table('permission_actions',
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['action_id'], ['action.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ),
        sa.PrimaryKeyConstraint('permission_id', 'action_id')
    )

    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    op.create_table('route_permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(length=256), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route', 'permission_id', name='_route_permission_uc')
    )


def downgrade():
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('route_permission')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permission_actions')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('permission')
    op.drop_table('action')
