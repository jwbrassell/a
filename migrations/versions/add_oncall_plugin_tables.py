"""add oncall plugin tables

Revision ID: add_oncall_plugin_tables
Revises: 266578b5c2bc
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_oncall_plugin_tables'
down_revision = '266578b5c2bc'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # Skip database_connection table creation if it exists
    if 'database_connection' not in tables:
        op.create_table('database_connection',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.String(length=256), nullable=True),
            sa.Column('db_type', sa.String(length=50), nullable=False),
            sa.Column('host', sa.String(length=256), nullable=True),
            sa.Column('port', sa.Integer(), nullable=True),
            sa.Column('database', sa.String(length=128), nullable=True),
            sa.Column('username', sa.String(length=128), nullable=True),
            sa.Column('password', sa.String(length=256), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_dbconn_user_id'),
            sa.PrimaryKeyConstraint('id', name='pk_database_connection')
        )

    # Create oncall_rotation table if it doesn't exist
    if 'oncall_rotation' not in tables:
        op.create_table('oncall_rotation',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('week_number', sa.Integer(), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('person_name', sa.String(length=100), nullable=False),
            sa.Column('phone_number', sa.String(length=20), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('end_time', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Add indexes for faster lookups
        op.create_index(op.f('ix_oncall_rotation_start_time'), 'oncall_rotation', ['start_time'], unique=False)
        op.create_index(op.f('ix_oncall_rotation_end_time'), 'oncall_rotation', ['end_time'], unique=False)
        op.create_index(op.f('ix_oncall_rotation_year_week'), 'oncall_rotation', ['year', 'week_number'], unique=True)


def downgrade():
    # Drop oncall_rotation indexes first
    op.drop_index(op.f('ix_oncall_rotation_start_time'), table_name='oncall_rotation')
    op.drop_index(op.f('ix_oncall_rotation_end_time'), table_name='oncall_rotation')
    op.drop_index(op.f('ix_oncall_rotation_year_week'), table_name='oncall_rotation')
    
    # Drop tables
    op.drop_table('oncall_rotation')
    op.drop_table('database_connection')
