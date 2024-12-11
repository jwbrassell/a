from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import InvalidRequestError
import sys
from app import db
from app.plugins.projects.models import (
    Project, Task, Todo, Comment, History,
    ProjectStatus, ProjectPriority
)

def check_table_exists(inspector, table_name):
    """Check if a table exists in the database"""
    return table_name in inspector.get_table_names()

def check_column_exists(inspector, table_name, column_name):
    """Check if a column exists in a table"""
    if not check_table_exists(inspector, table_name):
        return False
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)

def check_index_exists(inspector, table_name, index_name):
    """Check if an index exists on a table"""
    if not check_table_exists(inspector, table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)

def check_foreign_keys(inspector, table_name):
    """Check foreign key constraints"""
    if not check_table_exists(inspector, table_name):
        return []
    return inspector.get_foreign_keys(table_name)

def main():
    inspector = inspect(db.engine)
    
    # Tables that should exist
    required_tables = [
        'project', 'task', 'todo', 'comment', 'history',
        'project_status', 'project_priority',
        'project_watchers', 'project_stakeholders',
        'project_shareholders', 'project_roles',
        'task_dependencies'
    ]
    
    # Check tables
    print("\nChecking tables...")
    missing_tables = []
    for table in required_tables:
        if not check_table_exists(inspector, table):
            missing_tables.append(table)
            print(f"❌ Missing table: {table}")
        else:
            print(f"✅ Table exists: {table}")
    
    # Check important columns
    print("\nChecking important columns...")
    missing_columns = []
    
    # Project columns
    project_columns = [
        'id', 'name', 'summary', 'icon', 'description', 'status',
        'priority', 'percent_complete', 'is_private',
        'notify_task_created', 'notify_task_completed', 'notify_comments',
        'lead_id', 'created_at', 'updated_at'
    ]
    for col in project_columns:
        if not check_column_exists(inspector, 'project', col):
            missing_columns.append(('project', col))
            print(f"❌ Missing column: project.{col}")
        else:
            print(f"✅ Column exists: project.{col}")
    
    # Task columns
    task_columns = [
        'id', 'project_id', 'parent_id', 'name', 'summary',
        'description', 'status_id', 'priority_id', 'due_date',
        'position', 'list_position', 'assigned_to_id',
        'created_at', 'updated_at'
    ]
    for col in task_columns:
        if not check_column_exists(inspector, 'task', col):
            missing_columns.append(('task', col))
            print(f"❌ Missing column: task.{col}")
        else:
            print(f"✅ Column exists: task.{col}")
    
    # Check foreign keys
    print("\nChecking foreign key relationships...")
    fk_tables = {
        'project': ['lead_id'],
        'task': ['project_id', 'parent_id', 'status_id', 'priority_id', 'assigned_to_id'],
        'todo': ['project_id', 'task_id', 'assigned_to_id'],
        'comment': ['project_id', 'task_id', 'user_id'],
        'history': ['project_id', 'task_id', 'user_id']
    }
    
    missing_fks = []
    for table, fks in fk_tables.items():
        if not check_table_exists(inspector, table):
            continue
        existing_fks = [fk['constrained_columns'][0] for fk in check_foreign_keys(inspector, table)]
        for fk in fks:
            if fk not in existing_fks:
                missing_fks.append((table, fk))
                print(f"❌ Missing foreign key: {table}.{fk}")
            else:
                print(f"✅ Foreign key exists: {table}.{fk}")
    
    # Check indexes
    print("\nChecking indexes...")
    required_indexes = [
        ('project', 'ix_project_status'),
        ('project', 'ix_project_priority'),
        ('task', 'ix_task_project_id'),
        ('task', 'ix_task_status_id'),
        ('task', 'ix_task_priority_id'),
        ('todo', 'ix_todo_project_id'),
        ('todo', 'ix_todo_task_id'),
        ('comment', 'ix_comment_project_id'),
        ('comment', 'ix_comment_task_id'),
        ('history', 'ix_history_project_id'),
        ('history', 'ix_history_task_id')
    ]
    
    missing_indexes = []
    for table, index in required_indexes:
        if not check_table_exists(inspector, table):
            continue
        if not check_index_exists(inspector, table, index):
            missing_indexes.append((table, index))
            print(f"❌ Missing index: {table}.{index}")
        else:
            print(f"✅ Index exists: {table}.{index}")
    
    # Check data integrity
    print("\nChecking data integrity...")
    try:
        with db.engine.connect() as conn:
            # Check for orphaned tasks
            orphaned_tasks = conn.execute(text("""
                SELECT COUNT(*) FROM task 
                WHERE project_id NOT IN (SELECT id FROM project)
            """)).scalar()
            if orphaned_tasks > 0:
                print(f"⚠️ Found {orphaned_tasks} orphaned tasks!")
            else:
                print("✅ No orphaned tasks found")
            
            # Check for orphaned todos
            orphaned_todos = conn.execute(text("""
                SELECT COUNT(*) FROM todo 
                WHERE (project_id IS NOT NULL AND project_id NOT IN (SELECT id FROM project))
                OR (task_id IS NOT NULL AND task_id NOT IN (SELECT id FROM task))
            """)).scalar()
            if orphaned_todos > 0:
                print(f"⚠️ Found {orphaned_todos} orphaned todos!")
            else:
                print("✅ No orphaned todos found")
            
            # Check for circular task dependencies
            circular_deps = conn.execute(text("""
                WITH RECURSIVE task_tree AS (
                    SELECT task_id, dependency_id, 1 as depth
                    FROM task_dependencies
                    UNION ALL
                    SELECT tt.task_id, td.dependency_id, tt.depth + 1
                    FROM task_tree tt
                    JOIN task_dependencies td ON tt.dependency_id = td.task_id
                    WHERE tt.depth < 100
                )
                SELECT COUNT(*) FROM task_tree
                WHERE task_id = dependency_id
            """)).scalar()
            if circular_deps > 0:
                print(f"⚠️ Found {circular_deps} circular task dependencies!")
            else:
                print("✅ No circular task dependencies found")
    except Exception as e:
        print(f"⚠️ Error checking data integrity: {str(e)}")
    
    # Summary
    print("\n=== Database Check Summary ===")
    if missing_tables:
        print("\nMissing Tables:")
        for table in missing_tables:
            print(f"- {table}")
    
    if missing_columns:
        print("\nMissing Columns:")
        for table, column in missing_columns:
            print(f"- {table}.{column}")
    
    if missing_fks:
        print("\nMissing Foreign Keys:")
        for table, fk in missing_fks:
            print(f"- {table}.{fk}")
    
    if missing_indexes:
        print("\nMissing Indexes:")
        for table, index in missing_indexes:
            print(f"- {table}.{index}")
    
    if not any([missing_tables, missing_columns, missing_fks, missing_indexes]):
        print("\n✅ All database structures are up to date!")
    else:
        print("\n⚠️ Database migration needed!")
        print("Run 'flask db migrate' to generate migration")
        print("Then 'flask db upgrade' to apply changes")

if __name__ == '__main__':
    main()
