"""Basic CRUD operations for tasks."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from ...models import Project, Task, ProjectStatus, ProjectPriority, ValidationError
from app.plugins.projects import bp
from datetime import datetime
from .utils import (
    serialize_date,
    create_task_history,
    log_task_activity,
    track_task_changes,
    validate_task_data
)

@bp.route('/<int:project_id>/tasks', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id, parent_id=None).order_by(Task.position).all()
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in tasks]
    })

@bp.route('/<int:project_id>/task', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_task(project_id):
    """Create a new task for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Validate task data
    errors = validate_task_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Get status and priority objects
        status = ProjectStatus.query.filter_by(name=data.get('status')).first() if data.get('status') else None
        priority = ProjectPriority.query.filter_by(name=data.get('priority')).first() if data.get('priority') else None
        
        # Create task
        task = Task(
            name=data['name'],
            description=data.get('description', ''),
            status_id=status.id if status else None,
            priority_id=priority.id if priority else None,
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
            assigned_to_id=data.get('assigned_to_id'),
            project_id=project_id,
            parent_id=data.get('parent_id'),
            position=data.get('position', 0),
            list_position=data.get('list_position', 'todo')
        )
        
        # Validate task depth
        task.validate_depth()
        
        # Create history entry
        create_task_history(task, 'created', current_user.id, {
            'name': task.name,
            'description': task.description,
            'status': status.name if status else None,
            'priority': priority.name if priority else None,
            'due_date': serialize_date(task.due_date),
            'assigned_to_id': task.assigned_to_id
        })
        
        # Log activity
        log_task_activity(current_user.id, current_user.username, "Created", task.name)
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'task': task.to_dict()
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating task: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_task(task_id):
    """Get a specific task"""
    task = Task.query.get_or_404(task_id)
    return jsonify({
        'success': True,
        'task': task.to_dict()
    })

@bp.route('/task/<int:task_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_task(task_id):
    """Update a task"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    # Validate task data
    errors = validate_task_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Track changes
        changes = track_task_changes(task, data)
        
        if changes:
            # Update task fields
            for field, change in changes.items():
                setattr(task, field, change['new'])
            
            # Create history entry
            create_task_history(task, 'updated', current_user.id, changes)
            
            # Log activity
            log_task_activity(current_user.id, current_user.username, "Updated", task.name)
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'task': task.to_dict()
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating task: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    task_name = task.name
    
    try:
        # Create history entry
        create_task_history(task, 'deleted', current_user.id, {'name': task_name})
        
        # Log activity
        log_task_activity(current_user.id, current_user.username, "Deleted", task_name)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting task: {str(e)}'
        }), 500
