"""Add status and priority relations to Task model

Revision ID: task_status_priority_relations
Revises: add_todo_due_date
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

# revision identifiers, used by Alembic.
revision = 'task_status_priority_relations'
down_revision = 'add_todo_due_date'
branch_labels = None
depends_on = None

def table_exists(table_name):
    inspector = inspect(op.get_bind())
    return table_name in inspector.get_table_names()

def upgrade():
    conn = op.get_bind()
    
    # Drop temporary tables if they exist
    conn.execute(text("DROP TABLE IF EXISTS task_new;"))
    conn.execute(text("DROP TABLE IF EXISTS task_old;"))

    # Create default statuses
    conn.execute(text("""
        INSERT INTO project_status (name, color)
        SELECT 'open', 'secondary'
        WHERE NOT EXISTS (SELECT 1 FROM project_status WHERE name = 'open');
    """))
    conn.execute(text("""
        INSERT INTO project_status (name, color)
        SELECT 'in_progress', 'primary'
        WHERE NOT EXISTS (SELECT 1 FROM project_status WHERE name = 'in_progress');
    """))
    conn.execute(text("""
        INSERT INTO project_status (name, color)
        SELECT 'review', 'info'
        WHERE NOT EXISTS (SELECT 1 FROM project_status WHERE name = 'review');
    """))
    conn.execute(text("""
        INSERT INTO project_status (name, color)
        SELECT 'completed', 'success'
        WHERE NOT EXISTS (SELECT 1 FROM project_status WHERE name = 'completed');
    """))

    # Create default priorities
    conn.execute(text("""
        INSERT INTO project_priority (name, color)
        SELECT 'low', 'success'
        WHERE NOT EXISTS (SELECT 1 FROM project_priority WHERE name = 'low');
    """))
    conn.execute(text("""
        INSERT INTO project_priority (name, color)
        SELECT 'medium', 'warning'
        WHERE NOT EXISTS (SELECT 1 FROM project_priority WHERE name = 'medium');
    """))
    conn.execute(text("""
        INSERT INTO project_priority (name, color)
        SELECT 'high', 'danger'
        WHERE NOT EXISTS (SELECT 1 FROM project_priority WHERE name = 'high');
    """))

    # Create new task table
    op.create_table('task_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('priority', sa.String(50), nullable=True),
        sa.Column('status_id', sa.Integer(), nullable=True),
        sa.Column('priority_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['task.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['status_id'], ['project_status.id'], ),
        sa.ForeignKeyConstraint(['priority_id'], ['project_priority.id'], )
    )

    # Copy data from old table to new table
    conn.execute(text("""
        INSERT INTO task_new (
            id, project_id, parent_id, name, summary, description,
            status, priority, due_date, created_at, updated_at, assigned_to_id
        )
        SELECT 
            id, project_id, parent_id, name, summary, description,
            status, priority, due_date, created_at, updated_at, assigned_to_id
        FROM task;
    """))

    # Update status_id and priority_id based on existing status and priority names
    conn.execute(text("""
        UPDATE task_new
        SET status_id = (
            SELECT id FROM project_status 
            WHERE project_status.name = task_new.status
        );
    """))
    conn.execute(text("""
        UPDATE task_new
        SET priority_id = (
            SELECT id FROM project_priority 
            WHERE project_priority.name = task_new.priority
        );
    """))

    # Drop old table and rename new one
    op.drop_table('task')
    op.rename_table('task_new', 'task')

def downgrade():
    conn = op.get_bind()
    
    # Drop temporary tables if they exist
    conn.execute(text("DROP TABLE IF EXISTS task_new;"))
    conn.execute(text("DROP TABLE IF EXISTS task_old;"))

    # Create temporary table with old schema
    op.create_table('task_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('priority', sa.String(50), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['task.id'], ),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], )
    )

    # Copy data back, converting status_id and priority_id back to strings
    conn.execute(text("""
        INSERT INTO task_old (
            id, project_id, parent_id, name, summary, description,
            status, priority, due_date, created_at, updated_at, assigned_to_id
        )
        SELECT 
            t.id, t.project_id, t.parent_id, t.name, t.summary, t.description,
            COALESCE(ps.name, t.status), COALESCE(pp.name, t.priority),
            t.due_date, t.created_at, t.updated_at, t.assigned_to_id
        FROM task t
        LEFT JOIN project_status ps ON t.status_id = ps.id
        LEFT JOIN project_priority pp ON t.priority_id = pp.id;
    """))

    # Drop new table and rename old one back
    op.drop_table('task')
    op.rename_table('task_old', 'task')
