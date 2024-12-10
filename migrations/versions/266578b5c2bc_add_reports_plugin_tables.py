"""Add reports plugin tables

Revision ID: 266578b5c2bc
Revises: 8803065dd675
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '266578b5c2bc'
down_revision = '8803065dd675'
branch_labels = None
depends_on = None

def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # Create database_connection table if it doesn't exist
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

    # Create saved_view table if it doesn't exist
    if 'saved_view' not in tables:
        op.create_table('saved_view',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.String(length=256), nullable=True),
            sa.Column('connection_id', sa.Integer(), nullable=False),
            sa.Column('query', sa.Text(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['connection_id'], ['database_connection.id'], name='fk_view_connection_id'),
            sa.ForeignKeyConstraint(['created_by'], ['user.id'], name='fk_view_user_id'),
            sa.PrimaryKeyConstraint('id', name='pk_saved_view')
        )

def downgrade():
    op.drop_table('saved_view')
    op.drop_table('database_connection')
