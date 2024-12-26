"""add_activity_and_page_visit_tables

Revision ID: 0e0f82fe6038
Revises: 5640419beec1
Create Date: 2024-12-26 11:37:42.489675

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0e0f82fe6038'
down_revision = '5640419beec1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dispatch_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('donotreply_email', sa.String(length=120), nullable=False),
    sa.Column('teams', sa.JSON(), nullable=False),
    sa.Column('priorities', sa.JSON(), nullable=False),
    sa.Column('subject_format', sa.String(length=200), nullable=False),
    sa.Column('body_format', sa.Text(), nullable=False),
    sa.Column('signature', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('document_tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('metric_alerts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('metric_name', sa.String(length=128), nullable=False),
    sa.Column('condition', sa.String(length=64), nullable=False),
    sa.Column('threshold', sa.Float(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_triggered', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('metric_dashboards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('layout', sa.JSON(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('metric_type', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('metrics', schema=None) as batch_op:
        batch_op.create_index('idx_metrics_name_timestamp', ['name', 'timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_metrics_metric_type'), ['metric_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_metrics_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_metrics_timestamp'), ['timestamp'], unique=False)

    op.create_table('project_metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('metric_name', sa.String(length=64), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('context_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('project_metrics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_project_metrics_project_id'), ['project_id'], unique=False)

    op.create_table('workcenters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('dispatch_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=200), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('priority', sa.String(length=50), nullable=False),
    sa.Column('team', sa.String(length=120), nullable=False),
    sa.Column('team_email', sa.String(length=120), nullable=False),
    sa.Column('requester_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('ticket_number', sa.String(length=100), nullable=False),
    sa.Column('ticket_number_2', sa.String(length=100), nullable=True),
    sa.Column('rma_required', sa.Boolean(), nullable=True),
    sa.Column('bridge_info', sa.String(length=200), nullable=True),
    sa.Column('rma_notes', sa.Text(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('hostname', sa.String(length=200), nullable=False),
    sa.ForeignKeyConstraint(['requester_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_analytics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=64), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('action', sa.String(length=64), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('context_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('document_analytics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_analytics_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_analytics_document_id'), ['document_id'], unique=False)

    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=256), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_template', sa.Boolean(), nullable=True),
    sa.Column('template_name', sa.String(length=256), nullable=True),
    sa.Column('is_private', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['document_categories.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_documents_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_updated_at'), ['updated_at'], unique=False)

    op.create_table('feature_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('feature_name', sa.String(length=128), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=True),
    sa.Column('context_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('feature_usage', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_feature_usage_feature_name'), ['feature_name'], unique=False)

    op.create_table('handoff_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('workcenter_id', sa.Integer(), nullable=False),
    sa.Column('priorities', sa.JSON(), nullable=False),
    sa.Column('shifts', sa.JSON(), nullable=False),
    sa.Column('require_close_comment', sa.Boolean(), nullable=True),
    sa.Column('allow_close_with_comment', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['workcenter_id'], ['workcenters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('handoffs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('workcenter_id', sa.Integer(), nullable=False),
    sa.Column('assigned_to_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('closed_by_id', sa.Integer(), nullable=True),
    sa.Column('ticket', sa.String(length=100), nullable=False),
    sa.Column('hostname', sa.String(length=200), nullable=True),
    sa.Column('kirke', sa.String(length=200), nullable=True),
    sa.Column('priority', sa.String(length=50), nullable=False),
    sa.Column('from_shift', sa.String(length=100), nullable=True),
    sa.Column('to_shift', sa.String(length=100), nullable=False),
    sa.Column('has_bridge', sa.Boolean(), nullable=True),
    sa.Column('bridge_link', sa.String(length=500), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('close_comment', sa.Text(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['closed_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['workcenter_id'], ['workcenters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('page_visit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('route', sa.String(length=256), nullable=False),
    sa.Column('method', sa.String(length=10), nullable=False),
    sa.Column('status_code', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=256), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('resource_utilization',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('resource_id', sa.Integer(), nullable=False),
    sa.Column('resource_type', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('utilization', sa.Float(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('context_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('resource_utilization', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_resource_utilization_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_resource_utilization_resource_id'), ['resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_resource_utilization_resource_type'), ['resource_type'], unique=False)

    op.create_table('team_productivity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('metric_name', sa.String(length=64), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('context_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('team_productivity', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_team_productivity_team_id'), ['team_id'], unique=False)

    op.create_table('user_activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=True),
    sa.Column('resource', sa.String(length=128), nullable=True),
    sa.Column('details', sa.String(length=512), nullable=True),
    sa.Column('activity', sa.String(length=512), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_preference',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('value', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'key', name='_user_key_uc')
    )
    op.create_table('workcenter_members',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('workcenter_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['workcenter_id'], ['workcenters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_caches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('format', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('access_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_changes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('changed_by', sa.Integer(), nullable=False),
    sa.Column('changed_at', sa.DateTime(), nullable=True),
    sa.Column('change_type', sa.String(length=32), nullable=False),
    sa.Column('previous_content', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_shares',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('permission', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_tag_association',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['document_tags.id'], ),
    sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    op.drop_table('feature_votes')
    op.drop_table('report_history')
    op.drop_table('database_connections')
    op.drop_table('aws_configurations')
    op.drop_table('feature_requests')
    op.drop_table('database_reports')
    op.drop_table('feature_comments')
    op.drop_table('bug_report_screenshots')
    op.drop_table('aws_ec2_instances')
    op.drop_table('bug_reports')
    op.drop_table('report_tags_association')
    op.drop_table('report_tags')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('report_tags',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('report_tags_association',
    sa.Column('report_id', sa.INTEGER(), nullable=False),
    sa.Column('tag_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['database_reports.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['report_tags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('report_id', 'tag_id')
    )
    op.create_table('bug_reports',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('route', sa.VARCHAR(length=255), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=False),
    sa.Column('occurrence_type', sa.VARCHAR(length=20), nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), server_default=sa.text("'open'"), nullable=True),
    sa.Column('merged_with', sa.INTEGER(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('user_roles', sa.VARCHAR(length=500), nullable=True),
    sa.ForeignKeyConstraint(['merged_with'], ['bug_reports.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('aws_ec2_instances',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('aws_config_id', sa.INTEGER(), nullable=False),
    sa.Column('instance_id', sa.VARCHAR(length=100), nullable=False),
    sa.Column('region', sa.VARCHAR(length=50), nullable=False),
    sa.Column('instance_type', sa.VARCHAR(length=50), nullable=False),
    sa.Column('state', sa.VARCHAR(length=50), nullable=False),
    sa.Column('public_ip', sa.VARCHAR(length=45), nullable=True),
    sa.Column('private_ip', sa.VARCHAR(length=45), nullable=True),
    sa.Column('launch_time', sa.DATETIME(), nullable=False),
    sa.Column('tags', sqlite.JSON(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['aws_config_id'], ['aws_configurations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('instance_id')
    )
    op.create_table('bug_report_screenshots',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('bug_report_id', sa.INTEGER(), nullable=False),
    sa.Column('filename', sa.VARCHAR(length=255), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['bug_report_id'], ['bug_reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feature_comments',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('feature_request_id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('comment', sa.TEXT(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['feature_request_id'], ['feature_requests.id'], name='fk_feature_comment_request'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_feature_comment_user'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('database_reports',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('connection_id', sa.INTEGER(), nullable=False),
    sa.Column('query_config', sqlite.JSON(), nullable=False),
    sa.Column('column_config', sqlite.JSON(), nullable=False),
    sa.Column('is_public', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('created_by_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['connection_id'], ['database_connections.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feature_requests',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=False),
    sa.Column('page_url', sa.VARCHAR(length=500), nullable=False),
    sa.Column('screenshot_path', sa.VARCHAR(length=500), nullable=True),
    sa.Column('status', sa.VARCHAR(length=50), server_default=sa.text("'pending'"), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('created_by', sa.INTEGER(), nullable=False),
    sa.Column('impact_details', sqlite.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_feature_request_creator'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('aws_configurations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('regions', sqlite.JSON(), nullable=False),
    sa.Column('vault_path', sa.VARCHAR(length=255), nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('vault_path')
    )
    op.create_table('database_connections',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('db_type', sa.VARCHAR(length=20), nullable=False),
    sa.Column('host', sa.VARCHAR(length=255), nullable=True),
    sa.Column('port', sa.INTEGER(), nullable=True),
    sa.Column('database', sa.VARCHAR(length=255), nullable=False),
    sa.Column('vault_path', sa.VARCHAR(length=255), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('created_by_id', sa.INTEGER(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('vault_path')
    )
    op.create_table('report_history',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('report_id', sa.INTEGER(), nullable=False),
    sa.Column('changed_by_id', sa.INTEGER(), nullable=True),
    sa.Column('changed_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('changes', sqlite.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['report_id'], ['database_reports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feature_votes',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('feature_request_id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['feature_request_id'], ['feature_requests.id'], name='fk_feature_vote_request'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('feature_request_id', 'user_id', name='unique_feature_vote')
    )
    op.drop_table('document_tag_association')
    op.drop_table('document_shares')
    op.drop_table('document_changes')
    op.drop_table('document_caches')
    op.drop_table('workcenter_members')
    op.drop_table('user_preference')
    op.drop_table('user_activity')
    with op.batch_alter_table('team_productivity', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_team_productivity_team_id'))

    op.drop_table('team_productivity')
    with op.batch_alter_table('resource_utilization', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_resource_utilization_resource_type'))
        batch_op.drop_index(batch_op.f('ix_resource_utilization_resource_id'))
        batch_op.drop_index(batch_op.f('ix_resource_utilization_project_id'))

    op.drop_table('resource_utilization')
    op.drop_table('page_visit')
    op.drop_table('handoffs')
    op.drop_table('handoff_settings')
    with op.batch_alter_table('feature_usage', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_feature_usage_feature_name'))

    op.drop_table('feature_usage')
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_documents_updated_at'))
        batch_op.drop_index(batch_op.f('ix_documents_title'))
        batch_op.drop_index(batch_op.f('ix_documents_created_at'))
        batch_op.drop_index(batch_op.f('ix_documents_category_id'))

    op.drop_table('documents')
    with op.batch_alter_table('document_analytics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_analytics_document_id'))
        batch_op.drop_index(batch_op.f('ix_document_analytics_category'))

    op.drop_table('document_analytics')
    op.drop_table('dispatch_history')
    op.drop_table('workcenters')
    with op.batch_alter_table('project_metrics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_project_metrics_project_id'))

    op.drop_table('project_metrics')
    with op.batch_alter_table('metrics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_metrics_timestamp'))
        batch_op.drop_index(batch_op.f('ix_metrics_name'))
        batch_op.drop_index(batch_op.f('ix_metrics_metric_type'))
        batch_op.drop_index('idx_metrics_name_timestamp')

    op.drop_table('metrics')
    op.drop_table('metric_dashboards')
    op.drop_table('metric_alerts')
    op.drop_table('document_tags')
    op.drop_table('document_categories')
    op.drop_table('dispatch_settings')
    # ### end Alembic commands ###
