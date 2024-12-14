"""Utility functions for project management."""

from datetime import datetime
from ...models import History, UserActivity, ProjectStatus, ProjectPriority
from app.extensions import db
from app.models import PageRouteMapping

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
        created_by=project.created_by,  # Use the same created_by from the project
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

def validate_project_data(data, is_update=False):
    """Validate project data before creation/update"""
    errors = []
    
    # Only check required fields for creation or if explicitly updating them
    if not is_update:
        if not data.get('name'):
            errors.append('Project name is required')
            
        # Validate status exists if provided
        if 'status' in data:
            status = ProjectStatus.query.filter_by(name=data['status']).first()
            if not status:
                errors.append(f'Invalid project status: {data["status"]}')
                
        # Validate priority exists if provided
        if 'priority' in data:
            priority = ProjectPriority.query.filter_by(name=data['priority']).first()
            if not priority:
                errors.append(f'Invalid project priority: {data["priority"]}')
    
    elif 'name' in data:
        if not data['name']:
            errors.append('Project name cannot be empty')
            
        # For updates, only validate status/priority if they're being updated
        if 'status' in data:
            status = ProjectStatus.query.filter_by(name=data['status']).first()
            if not status:
                errors.append(f'Invalid project status: {data["status"]}')
                
        if 'priority' in data:
            priority = ProjectPriority.query.filter_by(name=data['priority']).first()
            if not priority:
                errors.append(f'Invalid project priority: {data["priority"]}')
    
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
    """Check if user can edit the project based on RBAC permissions"""
    if not user or not project:
        return False
        
    # Admin users always have access
    if any(role.name == 'admin' for role in user.roles):
        return True
        
    # Get the route mapping for the edit project endpoint
    mapping = PageRouteMapping.query.filter_by(route='projects.edit_project').first()
    
    if not mapping:
        # If no mapping exists, default to requiring authentication only
        return True
        
    # Get the set of role names required for this route
    required_roles = {role.name for role in mapping.allowed_roles}
    
    if not required_roles:
        # If no roles are specified, default to requiring authentication only
        return True
        
    # Get the set of user's role names
    user_roles = {role.name for role in user.roles}
    
    # Check if user has any of the required roles
    return bool(required_roles & user_roles)

def can_view_project(user, project):
    """Check if user can view the project based on RBAC permissions"""
    if not user or not project:
        return False
        
    # Public projects can be viewed by any authenticated user with appropriate role
    if not project.is_private:
        # Get the route mapping for the view project endpoint
        mapping = PageRouteMapping.query.filter_by(route='projects.view_project').first()
        
        if not mapping:
            # If no mapping exists, default to requiring authentication only
            return True
            
        # Get the set of role names required for this route
        required_roles = {role.name for role in mapping.allowed_roles}
        
        if not required_roles:
            # If no roles are specified, default to requiring authentication only
            return True
            
        # Get the set of user's role names
        user_roles = {role.name for role in user.roles}
        
        # Check if user has any of the required roles
        return bool(required_roles & user_roles)
    
    # For private projects, user must have edit permission
    return can_edit_project(user, project)

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
