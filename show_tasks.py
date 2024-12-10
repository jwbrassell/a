from app import create_app
from app.plugins.projects.models import Project, Task

app = create_app()

def print_task_tree(task, level=0):
    """Print task and its subtasks recursively"""
    indent = "  " * level
    status = task.status.name if task.status else 'No status'
    priority = task.priority.name if task.priority else 'No priority'
    assigned_to = task.assigned_to.username if task.assigned_to else 'Unassigned'
    
    print(f"{indent}Task ID: {task.id}")
    print(f"{indent}Name: {task.name}")
    print(f"{indent}Summary: {task.summary}")
    print(f"{indent}Status: {status}")
    print(f"{indent}Priority: {priority}")
    print(f"{indent}Assigned To: {assigned_to}")
    print(f"{indent}Due Date: {task.due_date}")
    print(f"{indent}Created: {task.created_at}")
    print(f"{indent}Updated: {task.updated_at}")
    print(f"{indent}Position: {task.position}")
    print(f"{indent}List Position: {task.list_position}")
    
    # Print todos
    if task.todos:
        print(f"{indent}Todos:")
        for todo in task.todos:
            print(f"{indent}  - [{('x' if todo.completed else ' ')}] {todo.description}")
            if todo.due_date:
                print(f"{indent}    Due: {todo.due_date}")
    
    # Print dependencies
    if task.dependencies.count() > 0:
        print(f"{indent}Dependencies:")
        for dep in task.dependencies:
            print(f"{indent}  - {dep.name} (ID: {dep.id})")
    
    print(f"{indent}" + "-" * 50)
    
    # Recursively print subtasks
    for subtask in task.subtasks:
        print_task_tree(subtask, level + 1)

with app.app_context():
    print("\n=== Tasks in Database ===")
    
    # Get all projects
    projects = Project.query.all()
    
    for project in projects:
        print(f"\nProject: {project.name} (ID: {project.id})")
        print("=" * 60)
        
        # Get top-level tasks (tasks without parent)
        tasks = Task.query.filter_by(project_id=project.id, parent_id=None).all()
        
        if not tasks:
            print("No tasks found")
            continue
        
        # Print task tree for each top-level task
        for task in tasks:
            print_task_tree(task)
