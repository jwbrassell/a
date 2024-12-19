"""Utility functions for subtask management."""

from flask import current_app
from flask_login import current_user
from datetime import datetime
from app.extensions import db
from app.models import UserActivity
from ..models import Task, History, ProjectStatus, ProjectPriority

def can_manage_subtask(user, subtask):
    """Check if a user can manage a subtask.
    
    Args:
        user: The user to check permissions for
        subtask: The subtask to check access to
        
    Returns:
        bool: True if user has management access, False otherwise
    """
    if not user or not subtask:
        return False
        
    # Admin users can manage all subtasks
    if any(role.name.lower() == 'administrator' for role in user.roles):
        return True
        
    # Project lead can manage all project subtasks
    if subtask.project and subtask.project.lead_id == user.id:
        return True
        
    # Parent task owner can manage subtasks
    if subtask.parent and subtask.parent.assigned_to_id == user.id:
        return True
        
    # Assigned user can manage their subtasks
    if subtask.assigned_to_id == user.id:
        return True
        
    return False

def validate_subtask_data(data, is_update=False):
    """Validate subtask data.
    
    Args:
        data: Dictionary containing subtask data
        is_update: Whether this is an update operation
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check required fields
        if not is_update and 'name' not in data:
            return False, 'Subtask name is required'
            
        if 'name' in data and not data['name']:
            return False, 'Subtask name cannot be empty'
            
        # Validate due date format if provided
        if 'due_date' in data and data['due_date']:
            try:
                datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return False, 'Invalid due date format. Use YYYY-MM-DD'
                
        # Validate status if provided
        if 'status' in data and data['status']:
            status = ProjectStatus.query.filter_by(name=data['status']).first()
            if not status:
                return False, f'Invalid status: {data["status"]}'
                
        # Validate priority if provided
        if 'priority' in data and data['priority']:
            priority = ProjectPriority.query.filter_by(name=data['priority']).first()
            if not priority:
                return False, f'Invalid priority: {data["priority"]}'
                
        return True, None
    except Exception as e:
        current_app.logger.error(f"Error validating subtask data: {str(e)}")
        return False, 'Error validating subtask data'

def track_subtask_history(subtask, action, details=None):
    """Create a history entry for a subtask action.
    
    Args:
        subtask: The subtask being acted upon
        action: The action being performed ('created', 'updated', 'deleted')
        details: Optional dictionary of additional details
    """
    try:
        history = History(
            entity_type='subtask',
            action=action,
            user_id=current_user.id,
            project_id=subtask.project_id,
            task_id=subtask.parent_id,
            details=details or {}
        )
        
        if subtask.project:
            subtask.project.history.append(history)
            
        return history
    except Exception as e:
        current_app.logger.error(f"Error creating subtask history: {str(e)}")
        return None

def track_subtask_activity(subtask, action, extra_details=None):
    """Track user activity for subtask actions.
    
    Args:
        subtask: The subtask being acted upon
        action: The action being performed
        extra_details: Optional additional details for the activity message
    """
    try:
        activity_message = f"{action} sub task: {subtask.name}"
        if subtask.parent:
            activity_message += f" for task: {subtask.parent.name}"
        if extra_details:
            activity_message += f" ({extra_details})"
            
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=activity_message
        )
        db.session.add(activity)
        return activity
    except Exception as e:
        current_app.logger.error(f"Error tracking subtask activity: {str(e)}")
        return None

def get_subtask_changes(subtask, data):
    """Calculate changes between current subtask state and new data.
    
    Args:
        subtask: The current subtask
        data: Dictionary containing new data
        
    Returns:
        dict: Dictionary of changes
    """
    try:
        changes = {}
        
        # Basic fields
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
        
        # Status
        if 'status' in data:
            new_status = ProjectStatus.query.filter_by(name=data['status']).first() if data['status'] else None
            old_status = subtask.status
            if ((new_status and not old_status) or 
                (not new_status and old_status) or 
                (new_status and old_status and subtask.status_id != new_status.id)):
                changes['status'] = {
                    'old': old_status.name if old_status else None,
                    'new': new_status.name if new_status else None
                }
        
        # Priority
        if 'priority' in data:
            new_priority = ProjectPriority.query.filter_by(name=data['priority']).first() if data['priority'] else None
            old_priority = subtask.priority
            if ((new_priority and not old_priority) or 
                (not new_priority and old_priority) or 
                (new_priority and old_priority and subtask.priority_id != new_priority.id)):
                changes['priority'] = {
                    'old': old_priority.name if old_priority else None,
                    'new': new_priority.name if new_priority else None
                }
        
        # Due date
        if 'due_date' in data:
            new_due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
            old_due_date = subtask.due_date
            if new_due_date != old_due_date:
                changes['due_date'] = {
                    'old': old_due_date.isoformat() if old_due_date else None,
                    'new': new_due_date.isoformat() if new_due_date else None
                }
        
        return changes
    except Exception as e:
        current_app.logger.error(f"Error calculating subtask changes: {str(e)}")
        return {}

def apply_subtask_changes(subtask, changes):
    """Apply changes to a subtask.
    
    Args:
        subtask: The subtask to update
        changes: Dictionary of changes to apply
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Basic fields
        basic_fields = ['name', 'summary', 'description', 'assigned_to_id']
        for field in basic_fields:
            if field in changes:
                setattr(subtask, field, changes[field]['new'])
        
        # Status
        if 'status' in changes:
            new_status = ProjectStatus.query.filter_by(name=changes['status']['new']).first()
            subtask.status_id = new_status.id if new_status else None
        
        # Priority
        if 'priority' in changes:
            new_priority = ProjectPriority.query.filter_by(name=changes['priority']['new']).first()
            subtask.priority_id = new_priority.id if new_priority else None
        
        # Due date
        if 'due_date' in changes:
            subtask.due_date = datetime.strptime(changes['due_date']['new'], '%Y-%m-%d').date() if changes['due_date']['new'] else None
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error applying subtask changes: {str(e)}")
        return False
