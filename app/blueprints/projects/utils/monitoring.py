"""Monitoring utilities for the projects plugin."""

import time
from functools import wraps
from flask import request, current_app
from datetime import datetime
import logging
from threading import Lock
import json

# Configure logging
logger = logging.getLogger('projects.monitoring')

class PerformanceMetrics:
    """Track performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self._lock = Lock()
    
    def record(self, category, operation, duration, status='success', details=None):
        """Record a performance metric"""
        with self._lock:
            key = f"{category}:{operation}"
            if key not in self.metrics:
                self.metrics[key] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'details': []
                }
            
            self.metrics[key]['count'] += 1
            self.metrics[key]['total_time'] += duration
            self.metrics[key]['min_time'] = min(self.metrics[key]['min_time'], duration)
            self.metrics[key]['max_time'] = max(self.metrics[key]['max_time'], duration)
            
            if status == 'success':
                self.metrics[key]['success_count'] += 1
            else:
                self.metrics[key]['error_count'] += 1
            
            if details:
                self.metrics[key]['details'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'duration': duration,
                    'status': status,
                    **details
                })
                # Keep only last 100 details
                self.metrics[key]['details'] = self.metrics[key]['details'][-100:]
    
    def get_metrics(self):
        """Get current metrics"""
        with self._lock:
            result = {}
            for key, data in self.metrics.items():
                avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
                result[key] = {
                    'count': data['count'],
                    'avg_time': avg_time,
                    'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                    'max_time': data['max_time'],
                    'success_rate': (data['success_count'] / data['count'] * 100) if data['count'] > 0 else 0,
                    'recent_details': data['details'][-5:]  # Only return most recent 5 details
                }
            return result
    
    def clear(self):
        """Clear all metrics"""
        with self._lock:
            self.metrics = {}

# Global metrics instance
performance_metrics = PerformanceMetrics()

def monitor_performance(category, operation=None):
    """Decorator to monitor performance of functions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            details = {
                'function': f.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                details['error'] = str(e)
                raise
            finally:
                duration = time.time() - start_time
                op = operation or f.__name__
                performance_metrics.record(category, op, duration, status, details)
        
        return decorated_function
    return decorator

def monitor_database(f):
    """Decorator to monitor database operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return monitor_performance('database')(f)(*args, **kwargs)
    return decorated_function

def monitor_cache(f):
    """Decorator to monitor cache operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return monitor_performance('cache')(f)(*args, **kwargs)
    return decorated_function

def monitor_api(f):
    """Decorator to monitor API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        status = 'success'
        details = {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path
        }
        
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            status = 'error'
            details['error'] = str(e)
            raise
        finally:
            duration = time.time() - start_time
            performance_metrics.record('api', request.endpoint, duration, status, details)
    
    return decorated_function

class QueryTracker:
    """Track database queries"""
    
    def __init__(self):
        self.queries = []
        self._lock = Lock()
    
    def record_query(self, query, duration):
        """Record a database query"""
        with self._lock:
            self.queries.append({
                'timestamp': datetime.utcnow().isoformat(),
                'query': str(query),
                'duration': duration
            })
            # Keep only last 1000 queries
            self.queries = self.queries[-1000:]
    
    def get_slow_queries(self, threshold=1.0):
        """Get queries that took longer than threshold seconds"""
        with self._lock:
            return [q for q in self.queries if q['duration'] > threshold]
    
    def clear(self):
        """Clear query history"""
        with self._lock:
            self.queries = []

# Global query tracker instance
query_tracker = QueryTracker()

def log_slow_operations():
    """Log slow operations for monitoring"""
    metrics = performance_metrics.get_metrics()
    
    for key, data in metrics.items():
        if data['max_time'] > 1.0:  # Log operations taking more than 1 second
            logger.warning(
                f"Slow operation detected - {key}:\n"
                f"Count: {data['count']}\n"
                f"Avg Time: {data['avg_time']:.2f}s\n"
                f"Max Time: {data['max_time']:.2f}s\n"
                f"Success Rate: {data['success_rate']:.1f}%"
            )
    
    slow_queries = query_tracker.get_slow_queries()
    if slow_queries:
        logger.warning(
            f"Slow queries detected:\n" +
            "\n".join(
                f"Query: {q['query']}\n"
                f"Duration: {q['duration']:.2f}s\n"
                f"Timestamp: {q['timestamp']}"
                for q in slow_queries
            )
        )

def get_performance_report():
    """Generate a performance report"""
    metrics = performance_metrics.get_metrics()
    slow_queries = query_tracker.get_slow_queries()
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'slow_queries': slow_queries,
        'summary': {
            'total_operations': sum(m['count'] for m in metrics.values()),
            'avg_success_rate': sum(m['success_rate'] for m in metrics.values()) / len(metrics) if metrics else 0,
            'slow_queries_count': len(slow_queries)
        }
    }
