"""Task management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity
from ..models import Project, Task, History
from app.plugins.projects import bp

@bp.route('/<int:project_id>/tasks', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    project = Project.query.get_or_404(project_id)
    return jsonify([task.to_dict() for task in project.tasks])

@bp.route('/<int:project_id>/task', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task(project_id):
    """Create a new task for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    task = Task(
        name=data['name'],
        description=data.get('description', ''),
        status=data.get('status', 'new'),
        priority=data.get('priority', 'medium'),
        due_date=data.get('due_date'),
        assigned_to=data.get('assigned_to'),
        created_by=current_user.id,
        project_id=project_id
    )
    
    # Create history entry
    history = History(
        entity_type='task',
        action='created',
        user_id=current_user.id,
        project_id=project.id,
        details=data
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created task: {task.name} for project: {project.name}"
    )
    
    db.session.add(task)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task created successfully',
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_task(task_id):
    """Get a specific task"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@bp.route('/task/<int:task_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task(task_id):
    """Update a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    # Track changes for history
    changes = {}
    for key, value in data.items():
        if hasattr(task, key) and getattr(task, key) != value:
            changes[key] = {'old': getattr(task, key), 'new': value}
            setattr(task, key, value)
    
    if changes:
        # Create history entry
        history = History(
            entity_type='task',
            action='updated',
            user_id=current_user.id,
            project_id=task.project_id,
            details=changes
        )
        task.project.history.append(history)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated task: {task.name}"
        )
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task updated successfully',
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    project = task.project
    task_name = task.name
    
    # Create history entry
    history = History(
        entity_type='task',
        action='deleted',
        user_id=current_user.id,
        project_id=project.id,
        details={'name': task_name}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted task: {task_name} from project: {project.name}"
    )
    
    db.session.add(activity)
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task deleted successfully'
    })

@bp.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def complete_task(task_id):
    """Mark a task as complete"""
    task = Task.query.get_or_404(task_id)
    task.status = 'completed'
    
    # Create history entry
    history = History(
        entity_type='task',
        action='completed',
        user_id=current_user.id,
        project_id=task.project_id,
        details={'status': 'completed'}
    )
    task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Completed task: {task.name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Task marked as complete',
        'task': task.to_dict()
    })
