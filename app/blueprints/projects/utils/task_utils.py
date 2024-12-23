"""Utility functions for task management."""

from flask import current_app
from flask_login import current_user
from sqlalchemy import and_
from datetime import datetime
from ..models import Task, History

def can_edit_task(user, task):
    """Check if a user can edit a task.
    
    Args:
        user: The user to check permissions for
        task: The task to check access to
        
    Returns:
        bool: True if user has edit access, False otherwise
    """
    if not user or not task:
        return False
        
    # Admin users can edit all tasks
    if any(role.name.lower() == 'administrator' for role in user.roles):
        return True
        
    # Project lead can edit all project tasks
    if task.project.lead_id == user.id:
        return True
        
    # Assigned user can edit their tasks
    if task.assigned_to_id == user.id:
        return True
        
    return False

def get_available_tasks(project_id, exclude_task_id=None):
    """Get available tasks for dependency selection.
    
    Args:
        project_id: The project ID to get tasks from
        exclude_task_id: Optional task ID to exclude (e.g., when editing a task)
        
    Returns:
        list: List of available tasks
    """
    try:
        query = Task.query.filter(Task.project_id == project_id)
        
        if exclude_task_id:
            query = query.filter(Task.id != exclude_task_id)
            
        return query.all()
    except Exception as e:
        current_app.logger.error(f"Error getting available tasks: {str(e)}")
        return []

def get_task_timeline(task, include_subtasks=True):
    """Get timeline of task activity.
    
    Args:
        task: The task to get timeline for
        include_subtasks: Whether to include subtask history
        
    Returns:
        list: List of timeline events
    """
    try:
        # Get all history entries for the task
        history_entries = []
        
        # Add task's own history
        history_entries.extend(task.history)
        
        # Add subtasks' history if requested
        if include_subtasks:
            for subtask in task.subtasks:
                history_entries.extend(subtask.history)
        
        # Add comment events
        for comment in task.comments:
            history_entries.append({
                'type': 'comment',
                'date': comment.created_at,
                'user': comment.user.username if comment.user else 'System',
                'content': comment.content,
                'icon': 'comment',
                'color': 'info'
            })
        
        # Sort by date descending
        history_entries.sort(key=lambda x: (
            x['date'] if isinstance(x, dict) else x.created_at
        ), reverse=True)
        
        return history_entries
    except Exception as e:
        current_app.logger.error(f"Error getting task timeline: {str(e)}")
        return []

def build_dependency_graph(task, max_depth=5):
    """Build dependency graph data for visualization.
    
    Args:
        task: The task to build graph for
        max_depth: Maximum depth to traverse
        
    Returns:
        tuple: (nodes, edges) for graph visualization
    """
    try:
        nodes = []
        edges = []
        visited = set()
        
        def add_task_to_graph(t, depth=0):
            if t.id in visited or depth > max_depth:
                return
            visited.add(t.id)
            
            # Add node
            nodes.append({
                'id': t.id,
                'label': t.name,
                'status': t.status.name if t.status else 'none',
                'priority': t.priority.name if t.priority else 'none',
                'assigned_to': t.assigned_to.username if t.assigned_to else 'Unassigned',
                'depth': depth,
                'due_date': t.due_date.isoformat() if t.due_date else None
            })
            
            # Add edges for dependencies
            for dep in t.dependencies:
                edges.append({
                    'from': t.id,
                    'to': dep.id,
                    'type': 'depends_on'
                })
                add_task_to_graph(dep, depth + 1)
            
            # Add edges for dependent tasks
            for dep in t.dependent_tasks:
                edges.append({
                    'from': dep.id,
                    'to': t.id,
                    'type': 'required_by'
                })
                add_task_to_graph(dep, depth + 1)
        
        add_task_to_graph(task)
        return nodes, edges
    except Exception as e:
        current_app.logger.error(f"Error building dependency graph: {str(e)}")
        return [], []

def get_task_stats(task):
    """Calculate statistics for a task.
    
    Args:
        task: The task to calculate statistics for
        
    Returns:
        dict: Dictionary containing task statistics
    """
    try:
        # Subtask statistics
        total_subtasks = len(task.subtasks)
        completed_subtasks = len([t for t in task.subtasks if t.list_position == 'completed'])
        
        # Todo statistics
        total_todos = len(task.todos)
        completed_todos = len([t for t in task.todos if t.completed])
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_subtasks > 0:
            subtask_weight = 0.7  # Subtasks are weighted more heavily
            todo_weight = 0.3
            
            subtask_completion = (completed_subtasks / total_subtasks) if total_subtasks > 0 else 0
            todo_completion = (completed_todos / total_todos) if total_todos > 0 else 0
            
            completion_percentage = (
                (subtask_completion * subtask_weight + todo_completion * todo_weight) * 100
            )
        elif total_todos > 0:
            completion_percentage = (completed_todos / total_todos) * 100
            
        return {
            'subtask_stats': {
                'total': total_subtasks,
                'completed': completed_subtasks,
                'completion_percentage': round(
                    (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0,
                    1
                )
            },
            'todo_stats': {
                'total': total_todos,
                'completed': completed_todos,
                'completion_percentage': round(
                    (completed_todos / total_todos * 100) if total_todos > 0 else 0,
                    1
                )
            },
            'overall_completion': round(completion_percentage, 1),
            'dependency_count': task.dependencies.count(),
            'dependent_count': task.dependent_tasks.count(),
            'comment_count': len(task.comments),
            'history_count': len(task.history)
        }
    except Exception as e:
        current_app.logger.error(f"Error calculating task stats: {str(e)}")
        return {
            'subtask_stats': {'total': 0, 'completed': 0, 'completion_percentage': 0},
            'todo_stats': {'total': 0, 'completed': 0, 'completion_percentage': 0},
            'overall_completion': 0,
            'dependency_count': 0,
            'dependent_count': 0,
            'comment_count': 0,
            'history_count': 0
        }
