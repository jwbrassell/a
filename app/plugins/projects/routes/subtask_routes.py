"""Sub Task management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity, User
from ..models import Task, History, ProjectStatus, ProjectPriority, Comment
from app.plugins.projects import bp
from datetime import datetime

@bp.route('/subtask/<int:subtask_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_subtask(subtask_id):
    """Get a specific sub task"""
    try:
        subtask = Task.query.get(subtask_id)
        if not subtask:
            return jsonify({
                'success': False,
                'message': 'Sub task not found'
            }), 404
            
        # Get status and priority options
        statuses = ProjectStatus.query.all()
        priorities = ProjectPriority.query.all()
        
        # Get all users for the lead dropdown
        users = User.query.all()
            
        return jsonify({
            'success': True,
            'subtask': subtask.to_dict(),
            'statuses': [status.to_dict() for status in statuses],
            'priorities': [priority.to_dict() for priority in priorities],
            'users': [{'id': user.id, 'username': user.username} for user in users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading sub task: {str(e)}'
        }), 500

@bp.route('/subtask/<int:subtask_id>/history', methods=['GET'])
@login_required
@requires_roles('user')
def get_subtask_history(subtask_id):
    """Get history for a specific sub task"""
    try:
        subtask = Task.query.get(subtask_id)
        if not subtask:
            return jsonify({
                'success': False,
                'message': 'Sub task not found'
            }), 404
            
        # Get history entries for this subtask
        history = History.query.filter_by(
            entity_type='subtask',
            task_id=subtask.parent_id,
            project_id=subtask.project_id
        ).order_by(History.created_at.desc()).all()
            
        return jsonify({
            'success': True,
            'history': [h.to_dict() for h in history]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading history: {str(e)}'
        }), 500

@bp.route('/task/<int:task_id>/subtask', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_subtask(task_id):
    """Create a new sub task"""
    parent_task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({
            'success': False,
            'message': 'Sub task name is required'
        }), 400
    
    # Parse due date if provided
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid due date format. Use YYYY-MM-DD'
            }), 400

    # Get status and priority objects
    status = None
    if data.get('status'):
        status = ProjectStatus.query.filter_by(name=data['status']).first()

    priority = None
    if data.get('priority'):
        priority = ProjectPriority.query.filter_by(name=data['priority']).first()
    
    subtask = Task(
        name=data['name'],
        summary=data.get('summary', ''),
        description=data.get('description', ''),
        status_id=status.id if status else None,
        priority_id=priority.id if priority else None,
        due_date=due_date,
        assigned_to_id=data.get('assigned_to_id'),
        project_id=parent_task.project_id,
        parent_id=task_id
    )
    
    # Create history entry
    history = History(
        entity_type='subtask',
        action='created',
        user_id=current_user.id,
        project_id=parent_task.project_id,
        task_id=parent_task.id,
        details={
            'name': subtask.name,
            'summary': subtask.summary,
            'description': subtask.description,
            'status': status.name if status else None,
            'priority': priority.name if priority else None,
            'due_date': subtask.due_date.isoformat() if subtask.due_date else None,
            'assigned_to_id': subtask.assigned_to_id
        }
    )
    parent_task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Created sub task: {subtask.name} for task: {parent_task.name}"
    )
    
    db.session.add(subtask)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Sub task created successfully',
        'subtask': subtask.to_dict()
    })

@bp.route('/subtask/<int:subtask_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_subtask(subtask_id):
    """Update a sub task"""
    subtask = Task.query.get_or_404(subtask_id)
    data = request.get_json()
    
    # Validate required fields if provided
    if 'name' in data and not data['name']:
        return jsonify({
            'success': False,
            'message': 'Sub task name cannot be empty'
        }), 400
    
    # Track changes for history
    changes = {}
    
    # Update basic fields
    basic_fields = ['name', 'summary', 'description', 'assigned_to_id']
    for field in basic_fields:
        if field in data:
            old_value = getattr(subtask, field)
            new_value = data[field]
            if new_value != old_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
                setattr(subtask, field, new_value)

    # Update status
    if 'status' in data:
        new_status = ProjectStatus.query.filter_by(name=data['status']).first() if data['status'] else None
        old_status = subtask.status
        if (new_status and not old_status) or (not new_status and old_status) or (new_status and old_status and subtask.status_id != new_status.id):
            changes['status'] = {
                'old': old_status.name if old_status else None,
                'new': new_status.name if new_status else None
            }
            subtask.status_id = new_status.id if new_status else None

    # Update priority
    if 'priority' in data:
        new_priority = ProjectPriority.query.filter_by(name=data['priority']).first() if data['priority'] else None
        old_priority = subtask.priority
        if (new_priority and not old_priority) or (not new_priority and old_priority) or (new_priority and old_priority and subtask.priority_id != new_priority.id):
            changes['priority'] = {
                'old': old_priority.name if old_priority else None,
                'new': new_priority.name if new_priority else None
            }
            subtask.priority_id = new_priority.id if new_priority else None
    
    # Update due date
    if 'due_date' in data:
        try:
            new_due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
            old_due_date = subtask.due_date
            if new_due_date != old_due_date:
                changes['due_date'] = {
                    'old': old_due_date.isoformat() if old_due_date else None,
                    'new': new_due_date.isoformat() if new_due_date else None
                }
                subtask.due_date = new_due_date
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid due date format. Use YYYY-MM-DD'
            }), 400
    
    if changes:
        # Create history entry
        history = History(
            entity_type='subtask',
            action='updated',
            user_id=current_user.id,
            project_id=subtask.project_id,
            task_id=subtask.parent_id,
            details=changes
        )
        subtask.project.history.append(history)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated sub task: {subtask.name}"
        )
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Sub task updated successfully',
        'subtask': subtask.to_dict()
    })

@bp.route('/subtask/<int:subtask_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_subtask(subtask_id):
    """Delete a sub task"""
    subtask = Task.query.get_or_404(subtask_id)
    parent_task = subtask.parent
    subtask_name = subtask.name
    
    # Create history entry
    history = History(
        entity_type='subtask',
        action='deleted',
        user_id=current_user.id,
        project_id=subtask.project_id,
        task_id=parent_task.id,
        details={'name': subtask_name}
    )
    parent_task.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted sub task: {subtask_name} from task: {parent_task.name}"
    )
    
    db.session.add(activity)
    db.session.delete(subtask)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Sub task deleted successfully'
    })

@bp.route('/subtask/<int:subtask_id>/comment', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_subtask_comment(subtask_id):
    """Add a comment to a sub task"""
    subtask = Task.query.get_or_404(subtask_id)
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({
            'success': False,
            'message': 'Comment content is required'
        }), 400
    
    comment = Comment(
        content=data['content'],
        task_id=subtask_id,
        user_id=current_user.id
    )
    
    # Create history entry
    history = History(
        entity_type='subtask',
        action='updated',
        user_id=current_user.id,
        project_id=subtask.project_id,
        task_id=subtask.parent_id,
        details={'comment_added': data['content'][:50] + '...' if len(data['content']) > 50 else data['content']}
    )
    subtask.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Added comment to sub task: {subtask.name}"
    )
    
    db.session.add(comment)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment added successfully',
        'comment': comment.to_dict()
    })

@bp.route('/subtask/<int:subtask_id>/comments', methods=['GET'])
@login_required
@requires_roles('user')
def get_subtask_comments(subtask_id):
    """Get all comments for a sub task"""
    subtask = Task.query.get_or_404(subtask_id)
    comments = Comment.query.filter_by(task_id=subtask_id).order_by(Comment.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'comments': [comment.to_dict() for comment in comments]
    })
