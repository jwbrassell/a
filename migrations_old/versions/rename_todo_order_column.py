"""rename todo order column

Revision ID: rename_todo_order_column
Revises: task_updates_migration
Create Date: 2024-12-08 21:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rename_todo_order_column'
down_revision = 'task_updates_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create new column
    op.add_column('todo', sa.Column('sort_order', sa.Integer(), nullable=True))
    
    # Copy data from old column if it exists
    try:
        op.execute('UPDATE todo SET sort_order = "order"')
    except:
        pass  # Column might not exist
    
    # Drop old column if it exists
    try:
        op.drop_column('todo', 'order')
    except:
        pass  # Column might not exist

def downgrade():
    # Create old column
    op.add_column('todo', sa.Column('order', sa.Integer(), nullable=True))
    
    # Copy data back
    op.execute('UPDATE todo SET "order" = sort_order')
    
    # Drop new column
    op.drop_column('todo', 'sort_order')
