"""Utility functions for project management."""

from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from ..models import ProjectStatus, ProjectPriority, Project, Task
from app.models import UserActivity

def can_manage_settings(user):
    """Check if a user can manage project settings.
    
    Args:
        user: The user to check permissions for
        
    Returns:
        bool: True if user has management access, False otherwise
    """
    return any(role.name.lower() == 'administrator' for role in user.roles)

def validate_color(color):
    """Validate a color value.
    
    Args:
        color: The color value to validate
        
    Returns:
        bool: True if color is valid, False otherwise
    """
    # Check if it's a hex color
    if color.startswith('#'):
        try:
            int(color[1:], 16)
            return len(color) in [4, 7]  # #RGB or #RRGGBB
        except ValueError:
            return False
    
    # Check if it's a Bootstrap color class
    bootstrap_colors = [
        'primary', 'secondary', 'success', 'danger',
        'warning', 'info', 'light', 'dark'
    ]
    return color in bootstrap_colors

def track_management_activity(action, details):
    """Track management activity.
    
    Args:
        action: The action being performed
        details: Dictionary of action details
    """
    try:
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Project management: {action}",
            details=details
        )
        db.session.add(activity)
    except Exception as e:
        current_app.logger.error(f"Error tracking management activity: {str(e)}")

def get_status_usage(status_name):
    """Get usage statistics for a status.
    
    Args:
        status_name: Name of the status to check
        
    Returns:
        dict: Dictionary containing usage statistics
    """
    try:
        projects_count = Project.query.filter_by(status=status_name).count()
        tasks_count = Task.query.join(ProjectStatus)\
            .filter(ProjectStatus.name == status_name).count()
            
        return {
            'projects_count': projects_count,
            'tasks_count': tasks_count,
            'is_in_use': projects_count > 0 or tasks_count > 0
        }
    except Exception as e:
        current_app.logger.error(f"Error getting status usage: {str(e)}")
        return {
            'projects_count': 0,
            'tasks_count': 0,
            'is_in_use': False
        }

def get_priority_usage(priority_name):
    """Get usage statistics for a priority.
    
    Args:
        priority_name: Name of the priority to check
        
    Returns:
        dict: Dictionary containing usage statistics
    """
    try:
        projects_count = Project.query.filter_by(priority=priority_name).count()
        tasks_count = Task.query.join(ProjectPriority)\
            .filter(ProjectPriority.name == priority_name).count()
            
        return {
            'projects_count': projects_count,
            'tasks_count': tasks_count,
            'is_in_use': projects_count > 0 or tasks_count > 0
        }
    except Exception as e:
        current_app.logger.error(f"Error getting priority usage: {str(e)}")
        return {
            'projects_count': 0,
            'tasks_count': 0,
            'is_in_use': False
        }

def bulk_update_status(old_name, new_name):
    """Update all references to a status.
    
    Args:
        old_name: Current status name
        new_name: New status name
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Update projects
        Project.query.filter_by(status=old_name)\
            .update({Project.status: new_name})
            
        # Update tasks
        old_status = ProjectStatus.query.filter_by(name=old_name).first()
        new_status = ProjectStatus.query.filter_by(name=new_name).first()
        if old_status and new_status:
            Task.query.filter_by(status_id=old_status.id)\
                .update({Task.status_id: new_status.id})
        
        db.session.commit()
        return True, "Status references updated successfully"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating status references: {str(e)}")
        return False, str(e)

def bulk_update_priority(old_name, new_name):
    """Update all references to a priority.
    
    Args:
        old_name: Current priority name
        new_name: New priority name
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Update projects
        Project.query.filter_by(priority=old_name)\
            .update({Project.priority: new_name})
            
        # Update tasks
        old_priority = ProjectPriority.query.filter_by(name=old_name).first()
        new_priority = ProjectPriority.query.filter_by(name=new_name).first()
        if old_priority and new_priority:
            Task.query.filter_by(priority_id=old_priority.id)\
                .update({Task.priority_id: new_priority.id})
        
        db.session.commit()
        return True, "Priority references updated successfully"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating priority references: {str(e)}")
        return False, str(e)

def get_management_stats():
    """Get project management statistics.
    
    Returns:
        dict: Dictionary containing management statistics
    """
    try:
        return {
            'status_count': ProjectStatus.query.count(),
            'priority_count': ProjectPriority.query.count(),
            'status_usage': {
                status.name: get_status_usage(status.name)
                for status in ProjectStatus.query.all()
            },
            'priority_usage': {
                priority.name: get_priority_usage(priority.name)
                for priority in ProjectPriority.query.all()
            }
        }
    except Exception as e:
        current_app.logger.error(f"Error getting management stats: {str(e)}")
        return {
            'status_count': 0,
            'priority_count': 0,
            'status_usage': {},
            'priority_usage': {}
        }
