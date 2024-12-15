"""Add handoff plugin tables

Revision ID: handoff_tables
Revises: 8d7a77b55ee5
Create Date: 2024-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'handoff_tables'
down_revision = '8d7a77b55ee5'
branch_labels = None
depends_on = None

def upgrade():
    # Create handoff_shifts table
    op.create_table('handoff_shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=32), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create handoffs table
    op.create_table('handoffs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to', sa.String(length=32), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False),
        sa.Column('ticket', sa.String(length=100), nullable=True),
        sa.Column('hostname', sa.String(length=100), nullable=True),
        sa.Column('kirke', sa.String(length=100), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('has_bridge', sa.Boolean(), nullable=True),
        sa.Column('bridge_link', sa.String(length=512), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert default shifts
    op.execute("""
        INSERT INTO handoff_shifts (name, description, created_at)
        VALUES 
        ('1st', 'First Shift', CURRENT_TIMESTAMP),
        ('2nd', 'Second Shift', CURRENT_TIMESTAMP),
        ('3rd', 'Third Shift', CURRENT_TIMESTAMP)
    """)

def downgrade():
    op.drop_table('handoffs')
    op.drop_table('handoff_shifts')
