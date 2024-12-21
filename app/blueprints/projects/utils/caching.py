"""Caching utilities for the projects plugin."""

from functools import wraps
from flask_caching import Cache
from datetime import datetime

cache = Cache()

def init_cache(app):
    """Initialize the cache with app config"""
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    cache.init_app(app, config=cache_config)

def cached_project(timeout=300):
    """Cache project data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(project_id, *args, **kwargs):
            cache_key = f'project_{project_id}'
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(project_id, *args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def cached_task(timeout=300):
    """Cache task data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(task_id, *args, **kwargs):
            cache_key = f'task_{task_id}'
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(task_id, *args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def cached_project_stats(timeout=60):
    """Cache project statistics"""
    def decorator(f):
        @wraps(f)
        def decorated_function(project_id, *args, **kwargs):
            cache_key = f'project_stats_{project_id}'
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(project_id, *args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def cached_user_projects(timeout=300):
    """Cache user's project list"""
    def decorator(f):
        @wraps(f)
        def decorated_function(user_id, *args, **kwargs):
            cache_key = f'user_projects_{user_id}'
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(user_id, *args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def cached_project_team(timeout=300):
    """Cache project team data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(project_id, *args, **kwargs):
            cache_key = f'project_team_{project_id}'
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(project_id, *args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator

def invalidate_project_cache(project_id):
    """Invalidate all cache entries related to a project"""
    keys_to_delete = [
        f'project_{project_id}',
        f'project_stats_{project_id}',
        f'project_team_{project_id}'
    ]
    
    # Also invalidate task caches for this project
    task_keys = cache.get(f'project_task_keys_{project_id}') or []
    keys_to_delete.extend(task_keys)
    
    for key in keys_to_delete:
        cache.delete(key)

def invalidate_task_cache(task_id, project_id=None):
    """Invalidate cache entries related to a task"""
    keys_to_delete = [f'task_{task_id}']
    
    if project_id:
        # Add task key to project's task keys
        task_keys = cache.get(f'project_task_keys_{project_id}') or []
        if f'task_{task_id}' not in task_keys:
            task_keys.append(f'task_{task_id}')
            cache.set(f'project_task_keys_{project_id}', task_keys)
        
        # Invalidate project stats
        keys_to_delete.append(f'project_stats_{project_id}')
    
    for key in keys_to_delete:
        cache.delete(key)

def invalidate_user_cache(user_id):
    """Invalidate user-related cache entries"""
    keys_to_delete = [
        f'user_projects_{user_id}'
    ]
    for key in keys_to_delete:
        cache.delete(key)

class CacheManager:
    """Manager class for handling cache operations"""
    
    @staticmethod
    def warm_project_cache(project_id):
        """Pre-warm cache for commonly accessed project data"""
        from ..models import Project
        
        project = Project.query.get(project_id)
        if not project:
            return
        
        # Cache project data
        cache.set(
            f'project_{project_id}',
            project.to_dict(),
            timeout=300
        )
        
        # Cache project stats
        from .projects import get_project_stats
        cache.set(
            f'project_stats_{project_id}',
            get_project_stats(project),
            timeout=60
        )
        
        # Cache project team
        cache.set(
            f'project_team_{project_id}',
            {
                'lead': project.lead.to_dict() if project.lead else None,
                'watchers': [u.to_dict() for u in project.watchers],
                'stakeholders': [u.to_dict() for u in project.stakeholders],
                'shareholders': [u.to_dict() for u in project.shareholders],
                'roles': [r.to_dict() for r in project.roles]
            },
            timeout=300
        )
    
    @staticmethod
    def warm_task_cache(task_id):
        """Pre-warm cache for commonly accessed task data"""
        from ..models import Task
        
        task = Task.query.get(task_id)
        if not task:
            return
        
        # Cache task data
        cache.set(
            f'task_{task_id}',
            task.to_dict(),
            timeout=300
        )
        
        # Add to project's task keys
        if task.project_id:
            task_keys = cache.get(f'project_task_keys_{task.project_id}') or []
            if f'task_{task_id}' not in task_keys:
                task_keys.append(f'task_{task_id}')
                cache.set(f'project_task_keys_{task.project_id}', task_keys)
    
    @staticmethod
    def clear_all_caches():
        """Clear all caches (use with caution)"""
        cache.clear()
