"""Add monitoring system tables

Revision ID: add_monitoring_tables
Revises: add_created_by_to_projects
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_monitoring_tables'
down_revision = 'add_created_by_to_projects'
branch_labels = None
depends_on = None

def upgrade():
    # System metrics table
    op.create_table('system_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metric_type', sa.String(length=50), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_metrics_timestamp', 'system_metrics', ['timestamp'])
    op.create_index('ix_system_metrics_metric_type', 'system_metrics', ['metric_type'])

    # Application metrics table
    op.create_table('application_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metric_type', sa.String(length=50), nullable=True),
        sa.Column('endpoint', sa.String(length=200), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_application_metrics_timestamp', 'application_metrics', ['timestamp'])
    op.create_index('ix_application_metrics_metric_type', 'application_metrics', ['metric_type'])
    op.create_index('ix_application_metrics_endpoint', 'application_metrics', ['endpoint'])

    # User metrics table
    op.create_table('user_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('metric_type', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_metrics_timestamp', 'user_metrics', ['timestamp'])
    op.create_index('ix_user_metrics_metric_type', 'user_metrics', ['metric_type'])

    # Feature usage table
    op.create_table('feature_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('feature', sa.String(length=100), nullable=True),
        sa.Column('plugin', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feature_usage_timestamp', 'feature_usage', ['timestamp'])
    op.create_index('ix_feature_usage_feature', 'feature_usage', ['feature'])
    op.create_index('ix_feature_usage_plugin', 'feature_usage', ['plugin'])

    # Resource metrics table
    op.create_table('resource_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resource_metrics_timestamp', 'resource_metrics', ['timestamp'])
    op.create_index('ix_resource_metrics_resource_type', 'resource_metrics', ['resource_type'])
    op.create_index('ix_resource_metrics_category', 'resource_metrics', ['category'])

def downgrade():
    op.drop_table('resource_metrics')
    op.drop_table('feature_usage')
    op.drop_table('user_metrics')
    op.drop_table('application_metrics')
    op.drop_table('system_metrics')
