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
    # Create independent tables first (no foreign key dependencies)
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

    # Create tables with self-referential foreign keys
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

    # Create tables that depend on the core tables
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

    # Create user table and its dependent tables last
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

    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create Database Reports blueprint tables
    op.create_table('database_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('db_type', sa.String(length=20), nullable=False),
        sa.Column('host', sa.String(length=255)),
        sa.Column('port', sa.Integer()),
        sa.Column('database', sa.String(length=255), nullable=False),
        sa.Column('vault_path', sa.String(length=255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('report_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('database_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('query_config', sa.JSON(), nullable=False),
        sa.Column('column_config', sa.JSON(), nullable=False),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['database_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('report_tags_association',
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['database_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['report_tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('report_id', 'tag_id')
    )

    op.create_table('report_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('changes', sa.JSON()),
        sa.ForeignKeyConstraint(['changed_by_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_id'], ['database_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create AWS Manager blueprint tables
    op.create_table('aws_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('regions', sa.JSON(), nullable=False),
        sa.Column('vault_path', sa.String(length=255), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('aws_ec2_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aws_config_id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('instance_type', sa.String(length=50), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('public_ip', sa.String(length=45)),
        sa.Column('private_ip', sa.String(length=45)),
        sa.Column('launch_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tags', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['aws_config_id'], ['aws_configurations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Bug Reports blueprint tables
    op.create_table('bug_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('occurrence_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='open'),
        sa.Column('merged_with', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('user_roles', sa.String(length=500)),
        sa.ForeignKeyConstraint(['merged_with'], ['bug_reports.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('feature_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page_url', sa.String(length=500), nullable=False),
        sa.Column('screenshot_path', sa.String(length=500)),
        sa.Column('status', sa.String(length=50), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('impact_details', sa.JSON()),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_feature_request_creator'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('bug_report_screenshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bug_report_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['bug_report_id'], ['bug_reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('feature_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['feature_request_id'], ['feature_requests.id'], name='fk_feature_comment_request'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_feature_comment_user'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('feature_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['feature_request_id'], ['feature_requests.id'], name='fk_feature_vote_request'),
        sa.UniqueConstraint('feature_request_id', 'user_id', name='unique_feature_vote'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('feature_votes')
    op.drop_table('feature_comments')
    op.drop_table('bug_report_screenshots')
    op.drop_table('feature_requests')
    op.drop_table('bug_reports')
    op.drop_table('aws_ec2_instances')
    op.drop_table('aws_configurations')
    op.drop_table('report_history')
    op.drop_table('report_tags_association')
    op.drop_table('database_reports')
    op.drop_table('report_tags')
    op.drop_table('database_connections')
    op.drop_table('route_permission')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permission_actions')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('permission')
    op.drop_table('action')
