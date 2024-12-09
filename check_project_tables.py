import sqlite3
import os

def check_db():
    """Check project plugin tables in SQLite database"""
    db_path = os.path.join('instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name;
    """)
    tables = cursor.fetchall()
    
    print("\n=== Existing Tables ===")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check project-related tables
    project_tables = [
        'project',
        'project_status',
        'project_priority',
        'project_watchers',
        'project_stakeholders',
        'project_shareholders',
        'project_roles',
        'task',
        'task_dependencies',
        'todo',
        'comment',
        'history'
    ]
    
    print("\n=== Project Plugin Tables Check ===")
    for table in project_tables:
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table}';
        """)
        if cursor.fetchone():
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"\n✅ Table '{table}' exists with columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  Total rows: {count}")
        else:
            print(f"\n❌ Missing table: {table}")
    
    # Check indexes
    print("\n=== Indexes Check ===")
    cursor.execute("""
        SELECT name, tbl_name 
        FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%'
        ORDER BY tbl_name, name;
    """)
    indexes = cursor.fetchall()
    
    if indexes:
        for idx in indexes:
            print(f"- {idx[1]}.{idx[0]}")
    else:
        print("No custom indexes found")
    
    # Check for potential issues
    print("\n=== Data Integrity Check ===")
    
    # Check for orphaned tasks
    cursor.execute("""
        SELECT COUNT(*) FROM task 
        WHERE project_id NOT IN (SELECT id FROM project);
    """)
    orphaned_tasks = cursor.fetchone()[0]
    if orphaned_tasks > 0:
        print(f"⚠️ Found {orphaned_tasks} tasks with invalid project_id")
    else:
        print("✅ No orphaned tasks found")
    
    # Check for orphaned todos
    cursor.execute("""
        SELECT COUNT(*) FROM todo 
        WHERE (project_id IS NOT NULL AND project_id NOT IN (SELECT id FROM project))
        OR (task_id IS NOT NULL AND task_id NOT IN (SELECT id FROM task));
    """)
    orphaned_todos = cursor.fetchone()[0]
    if orphaned_todos > 0:
        print(f"⚠️ Found {orphaned_todos} todos with invalid project_id or task_id")
    else:
        print("✅ No orphaned todos found")
    
    # Check for circular task dependencies
    cursor.execute("""
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
        WHERE task_id = dependency_id;
    """)
    circular_deps = cursor.fetchone()[0]
    if circular_deps > 0:
        print(f"⚠️ Found {circular_deps} circular task dependencies")
    else:
        print("✅ No circular task dependencies found")
    
    conn.close()

if __name__ == '__main__':
    check_db()
