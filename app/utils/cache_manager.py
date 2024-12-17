from functools import wraps
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from flask import current_app, request
from flask_caching import Cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask-Caching
cache = Cache()

class CacheManager:
    """Multi-level caching system for Flask applications."""
    
    def __init__(self, app=None):
        """Initialize cache manager with optional Flask app."""
        self.memory_cache = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize cache with Flask application."""
        # Initialize memory cache
        self.memory_cache = Cache(app, config={
            'CACHE_TYPE': 'SimpleCache',
            'CACHE_DEFAULT_TIMEOUT': 300
        })

    def warm_cache(self):
        """Warm up the cache with frequently accessed data."""
        try:
            # Warm up navigation data
            from app.models.navigation import Navigation
            nav_data = Navigation.get_all()
            self.memory_cache.set('navigation:all', nav_data, timeout=3600)
            
            # Warm up frequently accessed static data
            from app.models import Role
            roles = Role.query.all()
            self.memory_cache.set('roles:all', roles, timeout=3600)
            
            logger.info("Cache warming completed successfully")
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")

    def clear_all(self):
        """Clear all caches."""
        if self.memory_cache:
            self.memory_cache.clear()
        cache.clear()

    def clear_pattern(self, pattern: str):
        """Clear all cache entries matching a pattern."""
        # This is a basic implementation - could be enhanced based on needs
        self.clear_all()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        memory_stats = {
            'hits': 0,
            'misses': 0,
            'size': 0
        }
        
        if self.memory_cache:
            memory_stats = {
                'size': len(getattr(self.memory_cache.cache, '_cache', {})),
                'hits': getattr(self.memory_cache.cache, '_hits', 0),
                'misses': getattr(self.memory_cache.cache, '_misses', 0)
            }
        
        return {
            'memory_cache': memory_stats,
            'flask_cache': {
                'size': len(getattr(cache.cache, '_cache', {})),
                'hits': getattr(cache.cache, '_hits', 0),
                'misses': getattr(cache.cache, '_misses', 0)
            }
        }

    def update_performance_metrics(self, endpoint: str, duration: float):
        """Update performance metrics for an endpoint."""
        if not self.memory_cache:
            return
            
        metrics_key = f'metrics:{endpoint}'
        current_metrics = self.memory_cache.get(metrics_key) or {
            'count': 0,
            'total_duration': 0,
            'avg_duration': 0,
            'min_duration': float('inf'),
            'max_duration': 0
        }
        
        current_metrics['count'] += 1
        current_metrics['total_duration'] += duration
        current_metrics['avg_duration'] = (
            current_metrics['total_duration'] / current_metrics['count']
        )
        current_metrics['min_duration'] = min(
            current_metrics['min_duration'], 
            duration
        )
        current_metrics['max_duration'] = max(
            current_metrics['max_duration'], 
            duration
        )
        
        self.memory_cache.set(metrics_key, current_metrics, timeout=3600)

    def get_performance_metrics(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for an endpoint or all endpoints."""
        if not self.memory_cache:
            return {}
            
        if endpoint:
            metrics_key = f'metrics:{endpoint}'
            return self.memory_cache.get(metrics_key) or {}
        
        all_metrics = {}
        cache_dict = getattr(self.memory_cache.cache, '_cache', {})
        for key in cache_dict:
            if key.startswith('metrics:'):
                endpoint = key.split(':', 1)[1]
                all_metrics[endpoint] = self.memory_cache.get(key) or {}
        return all_metrics

# Initialize cache manager
cache_manager = CacheManager()

# Use Flask-Caching's decorators directly
cached = cache.cached
memoize = cache.memoize

def cache_response(timeout=300, key_prefix=''):
    """Cache decorator specifically for Flask view responses."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Don't cache for authenticated users or POST requests
            if request.method != 'GET' or getattr(request, 'user', None) is not None:
                return f(*args, **kwargs)

            return cache.cached(timeout=timeout, key_prefix=key_prefix)(f)(*args, **kwargs)
        return decorated_function
    return decorator
