"""Todo management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity, User
from ..models import Project, Task, Todo, History
from app.plugins.projects import bp
from datetime import datetime

@bp.route('/<int:project_id>/todos', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_todos(project_id):
    """Get all todos for a project"""
    project = Project.query.get_or_404(project_id)
    return jsonify([{
        'id': todo.id,
        'description': todo.description,
        'completed': todo.completed,
        'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
        'assigned_to': todo.assigned_to.username if todo.assigned_to else None,
        'created_at': todo.created_at.isoformat()
    } for todo in project.todos])

@bp.route('/task/<int:task_id>/todos', methods=['GET'])
@login_required
@requires_roles('user')
def get_task_todos(task_id):
    """Get all todos for a task"""
    task = Task.query.get_or_404(task_id)
    return jsonify([{
        'id': todo.id,
        'description': todo.description,
        'completed': todo.completed,
        'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
        'assigned_to': todo.assigned_to.username if todo.assigned_to else None,
        'created_at': todo.created_at.isoformat()
    } for todo in task.todos])

@bp.route('/<int:project_id>/todo', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_project_todo(project_id):
    """Create a new todo for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    todo = Todo(
        description=data['description'],
        project_id=project_id,
        assigned_to_id=data.get('assigned_to_id'),
        order=len(project.todos)  # Set order to end of list
    )
    
    # Create history entry
    history = History(
        entity_type='todo',
        action='created',
        user_id=current_user.id,
        project_id=project.id,
        details={'description': data['description']}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created todo in project: {project.name}"
    )
    
    db.session.add(todo)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Todo created successfully',
        'todo': {
            'id': todo.id,
            'description': todo.description,
            'completed': todo.completed,
            'assigned_to': todo.assigned_to.username if todo.assigned_to else None,
            'created_at': todo.created_at.isoformat()
        }
    })

@bp.route('/task/<int:task_id>/todo', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task_todo(task_id):
    """Create a new todo for a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    todo = Todo(
        description=data['description'],
        task_id=task_id,
        project_id=task.project_id,
        assigned_to_id=data.get('assigned_to_id'),
        order=len(task.todos)  # Set order to end of list
    )
    
    # Create history entry
    history = History(
        entity_type='todo',
        action='created',
        user_id=current_user.id,
        project_id=task.project_id,
        task_id=task_id,
        details={'description': data['description']}
    )
    task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created todo in task: {task.name}"
    )
    
    db.session.add(todo)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Todo created successfully',
        'todo': {
            'id': todo.id,
            'description': todo.description,
            'completed': todo.completed,
            'assigned_to': todo.assigned_to.username if todo.assigned_to else None,
            'created_at': todo.created_at.isoformat()
        }
    })

@bp.route('/todo/<int:todo_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_todo(todo_id):
    """Update a todo"""
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    
    # Track changes for history
    changes = {}
    if 'description' in data and data['description'] != todo.description:
        changes['description'] = {
            'old': todo.description,
            'new': data['description']
        }
        todo.description = data['description']
    
    if 'assigned_to_id' in data and data['assigned_to_id'] != todo.assigned_to_id:
        changes['assigned_to'] = {
            'old': todo.assigned_to.username if todo.assigned_to else None,
            'new': User.query.get(data['assigned_to_id']).username if data['assigned_to_id'] else None
        }
        todo.assigned_to_id = data['assigned_to_id']
    
    if changes:
        # Create history entry
        history = History(
            entity_type='todo',
            action='updated',
            user_id=current_user.id,
            project_id=todo.project_id,
            task_id=todo.task_id,
            details=changes
        )
        if todo.task:
            todo.task.project.history.append(history)
        else:
            todo.project.history.append(history)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated todo in {'task: ' + todo.task.name if todo.task else 'project: ' + todo.project.name}"
        )
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Todo updated successfully',
        'todo': {
            'id': todo.id,
            'description': todo.description,
            'completed': todo.completed,
            'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
            'assigned_to': todo.assigned_to.username if todo.assigned_to else None,
            'created_at': todo.created_at.isoformat()
        }
    })

@bp.route('/todo/<int:todo_id>/toggle', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def toggle_todo(todo_id):
    """Toggle a todo's completion status"""
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    todo.completed_at = datetime.utcnow() if todo.completed else None
    
    # Create history entry
    history = History(
        entity_type='todo',
        action='completed' if todo.completed else 'uncompleted',
        user_id=current_user.id,
        project_id=todo.project_id,
        task_id=todo.task_id,
        details={'completed_at': todo.completed_at.isoformat() if todo.completed_at else None}
    )
    if todo.task:
        todo.task.project.history.append(history)
    else:
        todo.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"{'Completed' if todo.completed else 'Uncompleted'} todo in {'task: ' + todo.task.name if todo.task else 'project: ' + todo.project.name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Todo {"completed" if todo.completed else "uncompleted"}',
        'todo': {
            'id': todo.id,
            'completed': todo.completed,
            'completed_at': todo.completed_at.isoformat() if todo.completed_at else None
        }
    })

@bp.route('/todo/reorder', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def reorder_todos():
    """Update the order of todos"""
    data = request.get_json()
    todos = data.get('todos', [])
    
    # Update order for each todo
    for todo_data in todos:
        todo = Todo.query.get(todo_data['id'])
        if todo:
            todo.order = todo_data['order']
    
    # Create history entry for the reordering
    if todos:
        # Get the project ID from the first todo
        first_todo = Todo.query.get(todos[0]['id'])
        if first_todo:
            history = History(
                entity_type='todo',
                action='reordered',
                user_id=current_user.id,
                project_id=first_todo.project_id,
                task_id=first_todo.task_id,
                details={'todo_orders': {str(t['id']): t['order'] for t in todos}}
            )
            if first_todo.task:
                first_todo.task.project.history.append(history)
            else:
                first_todo.project.history.append(history)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Reordered todos in {'task: ' + first_todo.task.name if first_todo.task else 'project: ' + first_todo.project.name}"
            )
            db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Todo order updated successfully'
    })

@bp.route('/todo/<int:todo_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_todo(todo_id):
    """Delete a todo"""
    todo = Todo.query.get_or_404(todo_id)
    project = todo.project
    task = todo.task
    
    # Create history entry
    history = History(
        entity_type='todo',
        action='deleted',
        user_id=current_user.id,
        project_id=project.id,
        task_id=task.id if task else None,
        details={'description': todo.description}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted todo from {'task: ' + task.name if task else 'project: ' + project.name}"
    )
    
    db.session.add(activity)
    db.session.delete(todo)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Todo deleted successfully'
    })
