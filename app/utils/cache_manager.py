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

class CacheManager:
    """Multi-level caching system for Flask applications."""
    
    def __init__(self, app=None):
        """Initialize cache manager with optional Flask app."""
        self.memory_cache = Cache(config={
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
        })
        
        self.filesystem_cache = Cache(config={
            'CACHE_TYPE': 'filesystem',
            'CACHE_DIR': 'instance/cache',
            'CACHE_DEFAULT_TIMEOUT': 3600,  # 1 hour
            'CACHE_THRESHOLD': 1000  # Maximum number of items
        })
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize cache with Flask application."""
        self.memory_cache.init_app(app)
        self.filesystem_cache.init_app(app)
        
        # Register cache management commands
        @app.cli.group()
        def cache():
            """Cache management commands."""
            pass

        @cache.command()
        def clear():
            """Clear all caches."""
            self.clear_all()
            logger.info("All caches cleared")

        @cache.command()
        def warm():
            """Warm up the cache with frequently accessed data."""
            self.warm_cache()
            logger.info("Cache warming completed")

        # Add cache stats to monitoring
        @app.before_request
        def before_request():
            request.start_time = datetime.utcnow()

        @app.after_request
        def after_request(response):
            if hasattr(request, 'start_time'):
                duration = (datetime.utcnow() - request.start_time).total_seconds()
                self.update_performance_metrics(request.endpoint, duration)
            return response

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key based on arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def cached(self, timeout=300, key_prefix='', unless=None):
        """Multi-level caching decorator."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if unless and unless():
                    return f(*args, **kwargs)

                cache_key = f"{key_prefix}:{self.generate_cache_key(*args, **kwargs)}"
                
                # Try memory cache first
                result = self.memory_cache.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    return result
                
                # Try filesystem cache
                result = self.filesystem_cache.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit (filesystem): {cache_key}")
                    # Store in memory for faster subsequent access
                    self.memory_cache.set(cache_key, result, timeout=timeout)
                    return result
                
                # Cache miss - execute function
                result = f(*args, **kwargs)
                
                # Store in both caches
                self.memory_cache.set(cache_key, result, timeout=timeout)
                self.filesystem_cache.set(cache_key, result, timeout=timeout)
                logger.debug(f"Cache miss: {cache_key}")
                
                return result
            return decorated_function
        return decorator

    def memoize(self, timeout=300):
        """Memoization decorator for class methods."""
        def decorator(f):
            @wraps(f)
            def decorated_function(instance, *args, **kwargs):
                cache_key = f"memo:{instance.__class__.__name__}:{f.__name__}:{self.generate_cache_key(*args, **kwargs)}"
                
                # Try memory cache
                result = self.memory_cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute and cache
                result = f(instance, *args, **kwargs)
                self.memory_cache.set(cache_key, result, timeout=timeout)
                return result
            return decorated_function
        return decorator

    def cache_response(self, timeout=300, key_prefix=''):
        """Cache decorator specifically for Flask view responses."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Don't cache for authenticated users or POST requests
                if request.method != 'GET' or getattr(request, 'user', None) is not None:
                    return f(*args, **kwargs)

                cache_key = f"view:{key_prefix}:{request.path}:{request.query_string.decode()}"
                
                # Try memory cache
                response = self.memory_cache.get(cache_key)
                if response is not None:
                    return response
                
                # Generate response
                response = f(*args, **kwargs)
                
                # Cache if response is successful
                if response.status_code == 200:
                    self.memory_cache.set(cache_key, response, timeout=timeout)
                
                return response
            return decorated_function
        return decorator

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
        self.memory_cache.clear()
        self.filesystem_cache.clear()

    def clear_pattern(self, pattern: str):
        """Clear all cache entries matching a pattern."""
        # This is a basic implementation - could be enhanced based on needs
        self.clear_all()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'memory_cache': {
                'size': len(self.memory_cache.cache._cache),
                'hits': getattr(self.memory_cache.cache, '_hits', 0),
                'misses': getattr(self.memory_cache.cache, '_misses', 0)
            },
            'filesystem_cache': {
                'size': len(self.filesystem_cache.cache._cache),
                'hits': getattr(self.filesystem_cache.cache, '_hits', 0),
                'misses': getattr(self.filesystem_cache.cache, '_misses', 0)
            }
        }

    def update_performance_metrics(self, endpoint: str, duration: float):
        """Update performance metrics for an endpoint."""
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
        if endpoint:
            metrics_key = f'metrics:{endpoint}'
            return self.memory_cache.get(metrics_key) or {}
        
        all_metrics = {}
        for key in self.memory_cache.cache._cache:
            if key.startswith('metrics:'):
                endpoint = key.split(':', 1)[1]
                all_metrics[endpoint] = self.memory_cache.get(key) or {}
        return all_metrics

# Initialize cache manager
cache_manager = CacheManager()

# Convenience decorators
def cached(timeout=300, key_prefix='', unless=None):
    """Convenience decorator for multi-level caching."""
    return cache_manager.cached(timeout=timeout, key_prefix=key_prefix, unless=unless)

def memoize(timeout=300):
    """Convenience decorator for memoization."""
    return cache_manager.memoize(timeout=timeout)

def cache_response(timeout=300, key_prefix=''):
    """Convenience decorator for response caching."""
    return cache_manager.cache_response(timeout=timeout, key_prefix=key_prefix)
