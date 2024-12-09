"""Todo management routes for projects."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from ...models import Project, Todo
from app.plugins.projects import bp
from datetime import datetime
from .utils import (
    create_project_history,
    log_project_activity,
    can_edit_project,
    serialize_date
)

@bp.route('/<int:project_id>/todos', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_todos(project_id):
    """Get all todos for a project"""
    project = Project.query.get_or_404(project_id)
    
    todos = Todo.query.filter_by(
        project_id=project_id,
        task_id=None  # Only get project-level todos
    ).order_by(Todo.sort_order).all()
    
    return jsonify({
        'success': True,
        'todos': [todo.to_dict() for todo in todos]
    })

@bp.route('/<int:project_id>/todos', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_project_todo(project_id):
    """Create a new project todo"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to create project todos'
        }), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('description'):
            return jsonify({
                'success': False,
                'message': 'Todo description is required'
            }), 400
        
        # Get the highest current sort_order
        max_order = db.session.query(db.func.max(Todo.sort_order)).filter_by(
            project_id=project_id,
            task_id=None
        ).scalar() or -1
        
        # Create todo
        todo = Todo(
            project_id=project_id,
            description=data['description'],
            completed=data.get('completed', False),
            sort_order=max_order + 1
        )
        
        # Handle due date
        if data.get('due_date'):
            try:
                todo.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid due date format. Use YYYY-MM-DD'
                }), 400
        
        # Create history entry
        create_project_history(project, 'todo_created', current_user.id, {
            'todo': {
                'description': todo.description,
                'due_date': serialize_date(todo.due_date)
            }
        })
        
        # Log activity
        log_project_activity(
            current_user.id,
            current_user.username,
            "Added todo to",
            project.name
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todo created successfully',
            'todo': todo.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating todo: {str(e)}'
        }), 500

@bp.route('/<int:project_id>/todos/reorder', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def reorder_project_todos(project_id):
    """Reorder project todos"""
    project = Project.query.get_or_404(project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to reorder project todos'
        }), 403
    
    try:
        data = request.get_json()
        todo_ids = data.get('todo_ids', [])
        
        # Track old positions
        old_positions = {
            todo.id: todo.sort_order
            for todo in Todo.query.filter(Todo.id.in_(todo_ids)).all()
        }
        
        # Update positions
        for index, todo_id in enumerate(todo_ids):
            Todo.query.filter_by(id=todo_id).update({
                'sort_order': index
            })
        
        # Create history entry
        create_project_history(project, 'todos_reordered', current_user.id, {
            'old_positions': old_positions,
            'new_positions': {id: idx for idx, id in enumerate(todo_ids)}
        })
        
        # Log activity
        log_project_activity(
            current_user.id,
            current_user.username,
            "Reordered todos in",
            project.name
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todos reordered successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error reordering todos: {str(e)}'
        }), 500

@bp.route('/todo/<int:todo_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_project_todo(todo_id):
    """Update a project todo"""
    todo = Todo.query.get_or_404(todo_id)
    project = Project.query.get(todo.project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update project todos'
        }), 403
    
    try:
        data = request.get_json()
        changes = {}
        
        # Update description
        if 'description' in data and data['description']:
            old_description = todo.description
            todo.description = data['description']
            changes['description'] = {
                'old': old_description,
                'new': todo.description
            }
        
        # Update completion status
        if 'completed' in data:
            old_completed = todo.completed
            todo.completed = data['completed']
            if todo.completed and not old_completed:
                todo.completed_at = datetime.utcnow()
            elif not todo.completed:
                todo.completed_at = None
            changes['completed'] = {
                'old': old_completed,
                'new': todo.completed
            }
        
        # Update due date
        if 'due_date' in data:
            old_date = serialize_date(todo.due_date)
            if data['due_date']:
                try:
                    todo.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid due date format. Use YYYY-MM-DD'
                    }), 400
            else:
                todo.due_date = None
            changes['due_date'] = {
                'old': old_date,
                'new': serialize_date(todo.due_date)
            }
        
        if changes:
            # Create history entry
            create_project_history(project, 'todo_updated', current_user.id, {
                'todo_id': todo.id,
                'changes': changes
            })
            
            # Log activity
            log_project_activity(
                current_user.id,
                current_user.username,
                "Updated todo in",
                project.name
            )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todo updated successfully',
            'todo': todo.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating todo: {str(e)}'
        }), 500

@bp.route('/todo/<int:todo_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_project_todo(todo_id):
    """Delete a project todo"""
    todo = Todo.query.get_or_404(todo_id)
    project = Project.query.get(todo.project_id)
    
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to delete project todos'
        }), 403
    
    try:
        # Create history entry
        create_project_history(project, 'todo_deleted', current_user.id, {
            'todo': {
                'id': todo.id,
                'description': todo.description,
                'completed': todo.completed,
                'due_date': serialize_date(todo.due_date)
            }
        })
        
        # Log activity
        log_project_activity(
            current_user.id,
            current_user.username,
            "Deleted todo from",
            project.name
        )
        
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todo deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting todo: {str(e)}'
        }), 500
