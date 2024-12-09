"""Utility functions for project management."""

from datetime import datetime
from ...models import History, UserActivity
from app.extensions import db

def serialize_date(date_obj):
    """Helper function to serialize date/datetime objects to ISO format strings"""
    if hasattr(date_obj, 'isoformat'):
        return date_obj.isoformat()
    return None

def create_project_history(project, action, user_id, details=None):
    """Create a history entry for a project action"""
    history = History(
        entity_type='project',
        action=action,
        user_id=user_id,
        project_id=project.id,
        details=details
    )
    project.history.append(history)
    return history

def log_project_activity(user_id, username, action, project_name):
    """Log a project-related activity"""
    activity = UserActivity(
        user_id=user_id,
        username=username,
        activity=f"{action} project: {project_name}"
    )
    db.session.add(activity)
    return activity

def track_project_changes(project, data):
    """Track changes made to a project"""
    changes = {}
    
    # Track basic field changes
    basic_fields = ['name', 'summary', 'description', 'status', 'priority', 
                   'percent_complete', 'lead_id', 'is_private']
    for field in basic_fields:
        if field in data:
            old_value = getattr(project, field)
            new_value = data[field]
            if new_value != old_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
    
    return changes

def validate_project_data(data):
    """Validate project data before creation/update"""
    errors = []
    
    # Required fields
    if not data.get('name'):
        errors.append('Project name is required')
    
    # Percent complete validation
    if 'percent_complete' in data:
        try:
            percent = int(data['percent_complete'])
            if percent < 0 or percent > 100:
                errors.append('Percent complete must be between 0 and 100')
        except (ValueError, TypeError):
            errors.append('Invalid percent complete value')
    
    return errors if errors else None

def can_edit_project(user, project):
    """Check if user can edit the project"""
    return (
        user.has_role('admin') or 
        project.lead_id == user.id
    )

def can_view_project(user, project):
    """Check if user can view the project"""
    if not project.is_private:
        return True
    
    return (
        user.has_role('admin') or
        project.lead_id == user.id or
        user in project.watchers or
        user in project.stakeholders or
        user in project.shareholders
    )

def get_project_stats(project):
    """Get project statistics"""
    total_tasks = len(project.tasks)
    completed_tasks = len([t for t in project.tasks if t.status and t.status.name == 'completed'])
    total_todos = len(project.todos)
    completed_todos = len([t for t in project.todos if t.completed])
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_todos': total_todos,
        'completed_todos': completed_todos,
        'task_completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'todo_completion_rate': (completed_todos / total_todos * 100) if total_todos > 0 else 0
    }
