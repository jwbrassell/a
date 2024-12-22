"""Utility functions for project management."""

from flask import current_app
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import Task, Comment, History

def can_edit_project(user, project):
    """Check if a user can edit a project.
    
    Args:
        user: The user to check permissions for
        project: The project to check access to
        
    Returns:
        bool: True if user has edit access, False otherwise
    """
    if not user or not project:
        return False
        
    # Project lead can always edit
    if project.lead_id == user.id:
        return True
        
    # Admin users can edit all projects
    if any(role.name.lower() == 'administrator' for role in user.roles):
        return True
        
    # Check if user has any required roles for the project
    user_roles = {role.name.lower() for role in user.roles}
    project_roles = {role.name.lower() for role in project.roles}
    
    return bool(user_roles & project_roles)

def can_view_project(user, project):
    """Check if a user can view a project.
    
    Args:
        user: The user to check permissions for
        project: The project to check access to
        
    Returns:
        bool: True if user has view access, False otherwise
    """
    if not user or not project:
        return False
        
    # Private projects require explicit access
    if project.is_private:
        # Check if user is project lead, watcher, stakeholder, or shareholder
        if (project.lead_id == user.id or
            user in project.watchers or
            user in project.stakeholders or
            user in project.shareholders):
            return True
            
        # Check if user has admin role
        if any(role.name.lower() == 'administrator' for role in user.roles):
            return True
            
        return False
    
    # Public projects just require authentication
    return True

def get_project_stats(project):
    """Calculate statistics for a project.
    
    Args:
        project: The project to calculate statistics for
        
    Returns:
        dict: Dictionary containing project statistics
    """
    try:
        # Task statistics
        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.list_position == 'completed'])
        overdue_tasks = len([t for t in project.tasks 
                           if t.due_date and t.due_date < datetime.utcnow().date() 
                           and t.list_position != 'completed'])
        
        # Activity statistics
        recent_activity = History.query.filter_by(project_id=project.id)\
            .order_by(History.created_at.desc())\
            .limit(5)\
            .all()
            
        # Comment statistics
        comment_count = Comment.query.filter_by(project_id=project.id).count()
        recent_comments = Comment.query.filter_by(project_id=project.id)\
            .order_by(Comment.created_at.desc())\
            .limit(3)\
            .all()
            
        # Team statistics
        team_members = set()
        if project.lead:
            team_members.add(project.lead.username)
        for task in project.tasks:
            if task.assigned_to:
                team_members.add(task.assigned_to.username)
                
        # Calculate completion percentage
        completion_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )
        
        # Calculate activity level (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_changes = History.query.filter(
            History.project_id == project.id,
            History.created_at >= week_ago
        ).count()
        
        return {
            'task_stats': {
                'total': total_tasks,
                'completed': completed_tasks,
                'overdue': overdue_tasks,
                'completion_percentage': round(completion_percentage, 1)
            },
            'activity_stats': {
                'recent_changes': recent_changes,
                'recent_activity': [h.to_dict() for h in recent_activity],
                'comment_count': comment_count,
                'recent_comments': [c.to_dict() for c in recent_comments]
            },
            'team_stats': {
                'member_count': len(team_members),
                'members': sorted(list(team_members))
            }
        }
    except Exception as e:
        current_app.logger.error(f"Error calculating project stats: {str(e)}")
        return {
            'task_stats': {'total': 0, 'completed': 0, 'overdue': 0, 'completion_percentage': 0},
            'activity_stats': {'recent_changes': 0, 'recent_activity': [], 'comment_count': 0, 'recent_comments': []},
            'team_stats': {'member_count': 0, 'members': []}
        }

def get_project_timeline(project, days=30):
    """Get timeline of project activity.
    
    Args:
        project: The project to get timeline for
        days: Number of days of history to include
        
    Returns:
        list: List of timeline events
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all relevant history entries
        history_entries = History.query.filter(
            History.project_id == project.id,
            History.created_at >= cutoff_date
        ).order_by(History.created_at.desc()).all()
        
        # Get all comments in time period
        comments = Comment.query.filter(
            Comment.project_id == project.id,
            Comment.created_at >= cutoff_date
        ).order_by(Comment.created_at.desc()).all()
        
        # Combine and sort all events
        timeline = []
        
        # Add history entries
        for entry in history_entries:
            timeline.append({
                'type': 'history',
                'date': entry.created_at,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.action,
                'details': entry.details,
                'icon': entry.icon,
                'color': entry.color
            })
            
        # Add comments
        for comment in comments:
            timeline.append({
                'type': 'comment',
                'date': comment.created_at,
                'user': comment.user.username if comment.user else 'System',
                'content': comment.content,
                'icon': 'comment',
                'color': 'info'
            })
            
        # Sort by date descending
        timeline.sort(key=lambda x: x['date'], reverse=True)
        
        return timeline
    except Exception as e:
        current_app.logger.error(f"Error getting project timeline: {str(e)}")
        return []
