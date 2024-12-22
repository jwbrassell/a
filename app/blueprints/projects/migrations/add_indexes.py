"""Add indexes for performance optimization."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_indexes_20240101'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Project indexes
    op.create_index('idx_project_status', 'project', ['status'])
    op.create_index('idx_project_priority', 'project', ['priority'])
    op.create_index('idx_project_lead', 'project', ['lead_id'])
    op.create_index('idx_project_updated', 'project', ['updated_at'])
    op.create_index('idx_project_created', 'project', ['created_at'])
    op.create_index('idx_project_complete', 'project', ['percent_complete'])
    op.create_index('idx_project_private', 'project', ['is_private'])

    # Task indexes
    op.create_index('idx_task_project', 'task', ['project_id'])
    op.create_index('idx_task_parent', 'task', ['parent_id'])
    op.create_index('idx_task_position', 'task', ['position'])
    op.create_index('idx_task_list_position', 'task', ['list_position'])
    op.create_index('idx_task_status', 'task', ['status_id'])
    op.create_index('idx_task_priority', 'task', ['priority_id'])
    op.create_index('idx_task_assigned', 'task', ['assigned_to_id'])
    op.create_index('idx_task_due_date', 'task', ['due_date'])
    op.create_index('idx_task_created', 'task', ['created_at'])
    op.create_index('idx_task_updated', 'task', ['updated_at'])
    
    # Composite indexes for common queries
    op.create_index(
        'idx_task_project_position',
        'task',
        ['project_id', 'position']
    )
    op.create_index(
        'idx_task_project_status',
        'task',
        ['project_id', 'status_id']
    )
    op.create_index(
        'idx_task_project_list',
        'task',
        ['project_id', 'list_position']
    )

    # Todo indexes
    op.create_index('idx_todo_project', 'todo', ['project_id'])
    op.create_index('idx_todo_task', 'todo', ['task_id'])
    op.create_index('idx_todo_order', 'todo', ['order'])
    op.create_index('idx_todo_completed', 'todo', ['completed'])
    op.create_index('idx_todo_due_date', 'todo', ['due_date'])
    op.create_index('idx_todo_created', 'todo', ['created_at'])
    
    # Composite indexes for todos
    op.create_index(
        'idx_todo_project_order',
        'todo',
        ['project_id', 'order']
    )
    op.create_index(
        'idx_todo_task_order',
        'todo',
        ['task_id', 'order']
    )

    # History indexes
    op.create_index('idx_history_project', 'history', ['project_id'])
    op.create_index('idx_history_task', 'history', ['task_id'])
    op.create_index('idx_history_user', 'history', ['user_id'])
    op.create_index('idx_history_created', 'history', ['created_at'])
    op.create_index('idx_history_type', 'history', ['entity_type'])
    op.create_index('idx_history_action', 'history', ['action'])
    
    # Composite indexes for history
    op.create_index(
        'idx_history_project_created',
        'history',
        ['project_id', 'created_at']
    )
    op.create_index(
        'idx_history_task_created',
        'history',
        ['task_id', 'created_at']
    )

    # Comment indexes
    op.create_index('idx_comment_project', 'comment', ['project_id'])
    op.create_index('idx_comment_task', 'comment', ['task_id'])
    op.create_index('idx_comment_user', 'comment', ['user_id'])
    op.create_index('idx_comment_created', 'comment', ['created_at'])
    
    # Composite indexes for comments
    op.create_index(
        'idx_comment_project_created',
        'comment',
        ['project_id', 'created_at']
    )
    op.create_index(
        'idx_comment_task_created',
        'comment',
        ['task_id', 'created_at']
    )

def downgrade():
    # Project indexes
    op.drop_index('idx_project_status')
    op.drop_index('idx_project_priority')
    op.drop_index('idx_project_lead')
    op.drop_index('idx_project_updated')
    op.drop_index('idx_project_created')
    op.drop_index('idx_project_complete')
    op.drop_index('idx_project_private')

    # Task indexes
    op.drop_index('idx_task_project')
    op.drop_index('idx_task_parent')
    op.drop_index('idx_task_position')
    op.drop_index('idx_task_list_position')
    op.drop_index('idx_task_status')
    op.drop_index('idx_task_priority')
    op.drop_index('idx_task_assigned')
    op.drop_index('idx_task_due_date')
    op.drop_index('idx_task_created')
    op.drop_index('idx_task_updated')
    
    # Composite task indexes
    op.drop_index('idx_task_project_position')
    op.drop_index('idx_task_project_status')
    op.drop_index('idx_task_project_list')

    # Todo indexes
    op.drop_index('idx_todo_project')
    op.drop_index('idx_todo_task')
    op.drop_index('idx_todo_order')
    op.drop_index('idx_todo_completed')
    op.drop_index('idx_todo_due_date')
    op.drop_index('idx_todo_created')
    
    # Composite todo indexes
    op.drop_index('idx_todo_project_order')
    op.drop_index('idx_todo_task_order')

    # History indexes
    op.drop_index('idx_history_project')
    op.drop_index('idx_history_task')
    op.drop_index('idx_history_user')
    op.drop_index('idx_history_created')
    op.drop_index('idx_history_type')
    op.drop_index('idx_history_action')
    
    # Composite history indexes
    op.drop_index('idx_history_project_created')
    op.drop_index('idx_history_task_created')

    # Comment indexes
    op.drop_index('idx_comment_project')
    op.drop_index('idx_comment_task')
    op.drop_index('idx_comment_user')
    op.drop_index('idx_comment_created')
    
    # Composite comment indexes
    op.drop_index('idx_comment_project_created')
    op.drop_index('idx_comment_task_created')
