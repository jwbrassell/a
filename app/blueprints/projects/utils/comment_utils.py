"""Utility functions for comment management."""

from flask import current_app
from flask_login import current_user
from datetime import datetime
from ..models import Comment, History, UserActivity
from app.extensions import db

def can_edit_comment(user, comment):
    """Check if a user can edit a comment.
    
    Args:
        user: The user to check permissions for
        comment: The comment to check access to
        
    Returns:
        bool: True if user has edit access, False otherwise
    """
    if not user or not comment:
        return False
        
    # Comment creator can edit
    if comment.user_id == user.id:
        return True
        
    # Admin users can edit all comments
    if any(role.name.lower() == 'administrator' for role in user.roles):
        return True
        
    # Project lead can edit project comments
    if comment.project and comment.project.lead_id == user.id:
        return True
        
    return False

def create_comment_history(comment, action, details=None):
    """Create a history entry for a comment action.
    
    Args:
        comment: The comment being acted upon
        action: The action being performed ('created', 'updated', 'deleted')
        details: Optional dictionary of additional details
        
    Returns:
        History: The created history entry
    """
    try:
        history = History(
            entity_type='comment',
            action=action,
            user_id=current_user.id,
            project_id=comment.project_id,
            task_id=comment.task_id,
            details=details or {}
        )
        
        if comment.project:
            comment.project.history.append(history)
            
        return history
    except Exception as e:
        current_app.logger.error(f"Error creating comment history: {str(e)}")
        return None

def track_comment_activity(comment, action):
    """Track user activity for comment actions.
    
    Args:
        comment: The comment being acted upon
        action: The action being performed ('added', 'updated', 'deleted')
        
    Returns:
        UserActivity: The created activity entry
    """
    try:
        context = 'task in ' if comment.task_id else ''
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"{action.capitalize()} comment in {context}project: {comment.project.name}"
        )
        db.session.add(activity)
        return activity
    except Exception as e:
        current_app.logger.error(f"Error tracking comment activity: {str(e)}")
        return None

def get_comment_stats(comment):
    """Get statistics for a comment.
    
    Args:
        comment: The comment to get statistics for
        
    Returns:
        dict: Dictionary containing comment statistics
    """
    try:
        return {
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
            'user': comment.user.username if comment.user else None,
            'project': comment.project.name if comment.project else None,
            'task': comment.task.name if comment.task else None,
            'content_length': len(comment.content),
            'has_been_edited': comment.updated_at is not None,
            'history_count': len([h for h in comment.project.history 
                                if h.entity_type == 'comment' and 
                                h.details.get('content') == comment.content])
        }
    except Exception as e:
        current_app.logger.error(f"Error getting comment stats: {str(e)}")
        return {
            'created_at': None,
            'updated_at': None,
            'user': None,
            'project': None,
            'task': None,
            'content_length': 0,
            'has_been_edited': False,
            'history_count': 0
        }

def notify_comment_subscribers(comment, action):
    """Notify relevant users about comment activity.
    
    Args:
        comment: The comment being acted upon
        action: The action being performed ('created', 'updated', 'deleted')
    """
    try:
        # Get list of users to notify
        subscribers = set()
        
        # Always notify project lead
        if comment.project and comment.project.lead:
            subscribers.add(comment.project.lead)
            
        # Notify task assignee if comment is on a task
        if comment.task and comment.task.assigned_to:
            subscribers.add(comment.task.assigned_to)
            
        # Notify project watchers if enabled
        if comment.project and comment.project.notify_comments:
            subscribers.update(comment.project.watchers)
            
        # Remove current user from notifications
        subscribers.discard(current_user)
        
        # Create notifications
        for user in subscribers:
            try:
                notification = {
                    'type': 'comment',
                    'action': action,
                    'user_id': user.id,
                    'comment_id': comment.id,
                    'project_id': comment.project_id,
                    'task_id': comment.task_id,
                    'created_at': datetime.utcnow(),
                    'read': False
                }
                
                # In a real implementation, you would:
                # 1. Save notification to database
                # 2. Emit websocket event
                # 3. Send email if user has email notifications enabled
                
                current_app.logger.info(
                    f"Would notify user {user.username} about comment {action}"
                )
                
            except Exception as e:
                current_app.logger.error(
                    f"Error creating notification for user {user.username}: {str(e)}"
                )
                
    except Exception as e:
        current_app.logger.error(f"Error notifying comment subscribers: {str(e)}")
