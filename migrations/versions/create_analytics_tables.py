"""Create analytics tables for business intelligence features.

Revision ID: create_analytics_tables
Revises: enhance_rbac_system
Create Date: 2024-01-01 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic
revision = 'create_analytics_tables'
down_revision = 'enhance_rbac_system'
branch_labels = None
depends_on = None

def upgrade():
    # Create feature_usage table
    op.create_table(
        'feature_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('action', sa.String(64), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('metadata', mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feature_usage_feature_name', 'feature_usage', ['feature_name'])
    op.create_index('ix_feature_usage_timestamp', 'feature_usage', ['timestamp'])

    # Create document_analytics table
    op.create_table(
        'document_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(64), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('action', sa.String(64), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('metadata', mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_analytics_document_id', 'document_analytics', ['document_id'])
    op.create_index('ix_document_analytics_category', 'document_analytics', ['category'])
    op.create_index('ix_document_analytics_timestamp', 'document_analytics', ['timestamp'])

    # Create project_metrics table
    op.create_table(
        'project_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(64), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', mysql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_metrics_project_id', 'project_metrics', ['project_id'])
    op.create_index('ix_project_metrics_timestamp', 'project_metrics', ['timestamp'])
    op.create_index('ix_project_metrics_metric_name', 'project_metrics', ['metric_name'])

    # Create team_productivity table
    op.create_table(
        'team_productivity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(64), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_team_productivity_team_id', 'team_productivity', ['team_id'])
    op.create_index('ix_team_productivity_timestamp', 'team_productivity', ['timestamp'])
    op.create_index('ix_team_productivity_metric_name', 'team_productivity', ['metric_name'])

    # Create resource_utilization table
    op.create_table(
        'resource_utilization',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('utilization', sa.Float(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('metadata', mysql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resource_utilization_resource_id', 'resource_utilization', ['resource_id'])
    op.create_index('ix_resource_utilization_resource_type', 'resource_utilization', ['resource_type'])
    op.create_index('ix_resource_utilization_project_id', 'resource_utilization', ['project_id'])
    op.create_index('ix_resource_utilization_start_time', 'resource_utilization', ['start_time'])

def downgrade():
    # Drop all tables in reverse order
    op.drop_table('resource_utilization')
    op.drop_table('team_productivity')
    op.drop_table('project_metrics')
    op.drop_table('document_analytics')
    op.drop_table('feature_usage')
