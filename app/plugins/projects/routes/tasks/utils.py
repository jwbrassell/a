"""Utility functions for task management."""

from datetime import datetime
from ...models import Task, History
from app.models import UserActivity
from app.extensions import db

def serialize_date(date_obj):
    """Helper function to serialize date/datetime objects to ISO format strings"""
    if hasattr(date_obj, 'isoformat'):
        return date_obj.isoformat()
    return None

def get_available_tasks(project_id, exclude_task_id=None):
    """Get available tasks for dependencies, excluding specified task and its descendants"""
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    if exclude_task_id:
        tasks = [t for t in tasks if t.id != exclude_task_id]
        
        # Filter out tasks that would create circular dependencies
        def is_descendant(task_a, task_b):
            if not task_b:
                return False
            if task_a.id == task_b.id:
                return True
            return any(is_descendant(task_a, subtask) for subtask in task_b.subtasks)
        
        exclude_task = Task.query.get(exclude_task_id)
        if exclude_task:
            tasks = [t for t in tasks if not is_descendant(t, exclude_task)]
    
    return tasks

def create_task_history(task, action, user_id, details=None):
    """Create a history entry for a task action"""
    history = History(
        entity_type='task',
        action=action,
        user_id=user_id,
        project_id=task.project_id,
        task_id=task.id,
        details=details
    )
    task.project.history.append(history)
    return history

def log_task_activity(user_id, username, action, task_name):
    """Log a task-related activity"""
    activity = UserActivity(
        user_id=user_id,
        username=username,
        activity=f"{action} task: {task_name}"
    )
    db.session.add(activity)
    return activity

def track_task_changes(task, data):
    """Track changes made to a task"""
    changes = {}
    
    # Track basic field changes
    basic_fields = ['name', 'summary', 'description', 'assigned_to_id', 'position', 'list_position']
    for field in basic_fields:
        if field in data:
            old_value = getattr(task, field)
            new_value = data[field]
            if new_value != old_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
    
    # Track status changes
    if 'status' in data and task.status:
        old_status = task.status.name if task.status else None
        if data['status'] != old_status:
            changes['status'] = {
                'old': old_status,
                'new': data['status']
            }
    
    # Track priority changes
    if 'priority' in data and task.priority:
        old_priority = task.priority.name if task.priority else None
        if data['priority'] != old_priority:
            changes['priority'] = {
                'old': old_priority,
                'new': data['priority']
            }
    
    # Track due date changes
    if 'due_date' in data:
        old_date = serialize_date(task.due_date)
        new_date = data['due_date']
        if new_date != old_date:
            changes['due_date'] = {
                'old': old_date,
                'new': new_date
            }
    
    return changes

def validate_task_data(data):
    """Validate task data before creation/update"""
    errors = []
    
    # Required fields
    if not data.get('name'):
        errors.append('Task name is required')
    
    # Due date format
    if data.get('due_date'):
        try:
            datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            errors.append('Invalid due date format. Use YYYY-MM-DD')
    
    # Return None if no errors, otherwise return list of errors
    return errors if errors else None
