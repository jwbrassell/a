"""add created_by to project tables

Revision ID: add_created_by_to_project_tables
Revises: merge_heads
Create Date: 2024-12-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_created_by_to_project_tables'
down_revision = 'merge_heads'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_by column to project_status
    op.add_column('project_status', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE project_status SET created_by = 'system'")
    op.alter_column('project_status', 'created_by', nullable=False)

    # Add created_by column to project_priority
    op.add_column('project_priority', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE project_priority SET created_by = 'system'")
    op.alter_column('project_priority', 'created_by', nullable=False)

    # Add created_by column to project
    op.add_column('project', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE project SET created_by = 'system'")
    op.alter_column('project', 'created_by', nullable=False)

    # Add created_by column to task
    op.add_column('task', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE task SET created_by = 'system'")
    op.alter_column('task', 'created_by', nullable=False)

    # Add created_by column to todo
    op.add_column('todo', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE todo SET created_by = 'system'")
    op.alter_column('todo', 'created_by', nullable=False)

    # Add created_by column to comment
    op.add_column('comment', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE comment SET created_by = 'system'")
    op.alter_column('comment', 'created_by', nullable=False)

    # Add created_by column to history
    op.add_column('history', sa.Column('created_by', sa.String(100), nullable=True))
    op.execute("UPDATE history SET created_by = 'system'")
    op.alter_column('history', 'created_by', nullable=False)

def downgrade():
    # Remove created_by columns
    op.drop_column('project_status', 'created_by')
    op.drop_column('project_priority', 'created_by')
    op.drop_column('project', 'created_by')
    op.drop_column('task', 'created_by')
    op.drop_column('todo', 'created_by')
    op.drop_column('comment', 'created_by')
    op.drop_column('history', 'created_by')
