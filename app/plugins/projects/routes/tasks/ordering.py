"""Task ordering and position management routes."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from ...models import Task
from app.plugins.projects import bp
from .utils import (
    create_task_history,
    log_task_activity
)

@bp.route('/<int:project_id>/tasks/reorder', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def reorder_tasks(project_id):
    """Reorder tasks in a project"""
    data = request.get_json()
    task_positions = data.get('task_positions', [])
    list_position = data.get('list_position')  # e.g., 'todo', 'in_progress', 'done'
    
    try:
        # Track old positions for history
        old_positions = {
            task.id: {'position': task.position, 'list_position': task.list_position}
            for task in Task.query.filter(Task.id.in_(task_positions)).all()
        }
        
        # Update task positions
        Task.reorder_tasks(project_id, task_positions)
        
        # Update list position if provided
        if list_position:
            Task.query.filter(Task.id.in_(task_positions)).update({
                Task.list_position: list_position
            }, synchronize_session=False)
        
        # Create history entry for the project
        task = Task.query.filter_by(project_id=project_id).first()
        if task:
            create_task_history(task, 'reordered', current_user.id, {
                'old_positions': old_positions,
                'new_positions': {
                    task_id: {'position': idx, 'list_position': list_position}
                    for idx, task_id in enumerate(task_positions)
                }
            })
            
            # Log activity
            log_task_activity(
                current_user.id,
                current_user.username,
                "Reordered tasks in project",
                task.project.name
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tasks reordered successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error reordering tasks: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>/move', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def move_task(task_id):
    """Move a task to a new position or list"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    try:
        changes = {}
        
        # Update position if provided
        if 'position' in data:
            old_position = task.position
            new_position = data['position']
            
            if old_position != new_position:
                task.position = new_position
                changes['position'] = {
                    'old': old_position,
                    'new': new_position
                }
        
        # Update list position if provided
        if 'list_position' in data:
            old_list = task.list_position
            new_list = data['list_position']
            
            if old_list != new_list:
                task.list_position = new_list
                changes['list_position'] = {
                    'old': old_list,
                    'new': new_list
                }
        
        if changes:
            # Create history entry
            create_task_history(task, 'moved', current_user.id, changes)
            
            # Log activity
            action = "Moved"
            if 'list_position' in changes:
                action = f"Moved to {changes['list_position']['new']}"
            log_task_activity(current_user.id, current_user.username, action, task.name)
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task moved successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error moving task: {str(e)}'
        }), 500

@bp.route('/<int:project_id>/tasks/positions', methods=['GET'])
@login_required
@requires_roles('user')
def get_task_positions(project_id):
    """Get current task positions for a project"""
    tasks = Task.query.filter_by(project_id=project_id).order_by(
        Task.list_position,
        Task.position
    ).all()
    
    # Group tasks by list position
    tasks_by_list = {}
    for task in tasks:
        list_pos = task.list_position or 'uncategorized'
        if list_pos not in tasks_by_list:
            tasks_by_list[list_pos] = []
        tasks_by_list[list_pos].append(task.to_dict())
    
    return jsonify({
        'success': True,
        'positions': tasks_by_list
    })

@bp.route('/<int:project_id>/tasks/kanban', methods=['GET'])
@login_required
@requires_roles('user')
def get_kanban_board(project_id):
    """Get tasks organized for kanban board view"""
    tasks = Task.query.filter_by(project_id=project_id).order_by(
        Task.position
    ).all()
    
    # Define standard kanban columns
    columns = {
        'todo': [],
        'in_progress': [],
        'review': [],
        'done': []
    }
    
    # Group tasks by list position
    for task in tasks:
        list_pos = task.list_position or 'todo'
        if list_pos not in columns:
            columns[list_pos] = []
        columns[list_pos].append(task.to_dict())
    
    return jsonify({
        'success': True,
        'columns': columns
    })

@bp.route('/<int:project_id>/tasks/reorder-batch', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def reorder_tasks_batch(project_id):
    """Reorder multiple tasks across different lists"""
    data = request.get_json()
    updates = data.get('updates', [])  # List of {task_id, position, list_position}
    
    try:
        changes = {}
        for update in updates:
            task_id = update.get('task_id')
            task = Task.query.get(task_id)
            
            if task and task.project_id == project_id:
                old_pos = task.position
                old_list = task.list_position
                new_pos = update.get('position')
                new_list = update.get('list_position')
                
                if new_pos is not None:
                    task.position = new_pos
                if new_list is not None:
                    task.list_position = new_list
                
                if old_pos != new_pos or old_list != new_list:
                    changes[task_id] = {
                        'position': {'old': old_pos, 'new': new_pos},
                        'list_position': {'old': old_list, 'new': new_list}
                    }
        
        if changes:
            # Create history entry for the project
            task = Task.query.filter_by(project_id=project_id).first()
            if task:
                create_task_history(task, 'batch_reordered', current_user.id, changes)
                
                # Log activity
                log_task_activity(
                    current_user.id,
                    current_user.username,
                    "Batch reordered tasks in project",
                    task.project.name
                )
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tasks reordered successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error reordering tasks: {str(e)}'
        }), 500
