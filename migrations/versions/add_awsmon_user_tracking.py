"""Add user tracking and soft delete to AWS Monitor plugin tables.

Revision ID: add_awsmon_user_tracking
Revises: enhance_rbac_system
Create Date: 2024-01-10 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic
revision = 'add_awsmon_user_tracking'
down_revision = 'enhance_rbac_system'
branch_labels = None
depends_on = None

def upgrade():
    # Add user tracking and soft delete columns to awsmon_regions
    op.add_column('awsmon_regions', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_regions', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_regions', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_regions_creator', 'awsmon_regions', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_regions_updater', 'awsmon_regions', 'user', ['updated_by'], ['id'])

    # Add user tracking and soft delete columns to awsmon_instances
    op.add_column('awsmon_instances', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_instances', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_instances', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_instances_creator', 'awsmon_instances', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_instances_updater', 'awsmon_instances', 'user', ['updated_by'], ['id'])

    # Add user tracking and soft delete columns to awsmon_jump_server_templates
    op.add_column('awsmon_jump_server_templates', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_jump_server_templates', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_jump_server_templates', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_templates_creator', 'awsmon_jump_server_templates', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_templates_updater', 'awsmon_jump_server_templates', 'user', ['updated_by'], ['id'])

    # Add user tracking and soft delete columns to awsmon_synthetic_tests
    op.add_column('awsmon_synthetic_tests', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_synthetic_tests', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_synthetic_tests', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_tests_creator', 'awsmon_synthetic_tests', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_tests_updater', 'awsmon_synthetic_tests', 'user', ['updated_by'], ['id'])

    # Add user tracking to awsmon_test_results (no soft delete needed for historical data)
    op.add_column('awsmon_test_results', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_results_creator', 'awsmon_test_results', 'user', ['created_by'], ['id'])

    # Add user tracking and soft delete columns to awsmon_credentials
    op.add_column('awsmon_credentials', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_credentials', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('awsmon_credentials', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_credentials_creator', 'awsmon_credentials', 'user', ['created_by'], ['id'])
    op.create_foreign_key('fk_credentials_updater', 'awsmon_credentials', 'user', ['updated_by'], ['id'])

    # Add user tracking to awsmon_changelog (no soft delete needed for historical data)
    op.add_column('awsmon_changelog', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_changelog_creator', 'awsmon_changelog', 'user', ['created_by'], ['id'])

def downgrade():
    # Remove foreign keys first
    op.drop_constraint('fk_regions_creator', 'awsmon_regions', type_='foreignkey')
    op.drop_constraint('fk_regions_updater', 'awsmon_regions', type_='foreignkey')
    op.drop_constraint('fk_instances_creator', 'awsmon_instances', type_='foreignkey')
    op.drop_constraint('fk_instances_updater', 'awsmon_instances', type_='foreignkey')
    op.drop_constraint('fk_templates_creator', 'awsmon_jump_server_templates', type_='foreignkey')
    op.drop_constraint('fk_templates_updater', 'awsmon_jump_server_templates', type_='foreignkey')
    op.drop_constraint('fk_tests_creator', 'awsmon_synthetic_tests', type_='foreignkey')
    op.drop_constraint('fk_tests_updater', 'awsmon_synthetic_tests', type_='foreignkey')
    op.drop_constraint('fk_results_creator', 'awsmon_test_results', type_='foreignkey')
    op.drop_constraint('fk_credentials_creator', 'awsmon_credentials', type_='foreignkey')
    op.drop_constraint('fk_credentials_updater', 'awsmon_credentials', type_='foreignkey')
    op.drop_constraint('fk_changelog_creator', 'awsmon_changelog', type_='foreignkey')

    # Remove columns
    op.drop_column('awsmon_regions', 'created_by')
    op.drop_column('awsmon_regions', 'updated_by')
    op.drop_column('awsmon_regions', 'deleted_at')

    op.drop_column('awsmon_instances', 'created_by')
    op.drop_column('awsmon_instances', 'updated_by')
    op.drop_column('awsmon_instances', 'deleted_at')

    op.drop_column('awsmon_jump_server_templates', 'created_by')
    op.drop_column('awsmon_jump_server_templates', 'updated_by')
    op.drop_column('awsmon_jump_server_templates', 'deleted_at')

    op.drop_column('awsmon_synthetic_tests', 'created_by')
    op.drop_column('awsmon_synthetic_tests', 'updated_by')
    op.drop_column('awsmon_synthetic_tests', 'deleted_at')

    op.drop_column('awsmon_test_results', 'created_by')

    op.drop_column('awsmon_credentials', 'created_by')
    op.drop_column('awsmon_credentials', 'updated_by')
    op.drop_column('awsmon_credentials', 'deleted_at')

    op.drop_column('awsmon_changelog', 'created_by')
