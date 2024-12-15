"""add due_date to todo

Revision ID: add_todo_due_date
Revises: task_updates_migration
Create Date: 2024-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_todo_due_date'
down_revision = 'task_updates_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Add due_date column to todo table
    op.add_column('todo', sa.Column('due_date', sa.Date(), nullable=True))

def downgrade():
    # Remove due_date column from todo table
    op.drop_column('todo', 'due_date')
