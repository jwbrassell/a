"""Metrics collection utility for application monitoring."""

import psutil
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from flask import current_app, request
from app.extensions import db, cache_manager
from app.utils.websocket_service import monitoring_ns
from dataclasses import dataclass
import json

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Represents a single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: str  # gauge, counter, histogram

class MetricsCollector:
    """Collects and manages application metrics."""

    def __init__(self, app=None):
        """Initialize metrics collector."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        
        # Register before_request handler
        app.before_request(self._before_request)
        
        # Register after_request handler
        app.after_request(self._after_request)
        
        # Start background collection if enabled
        if app.config.get('METRICS_ENABLED', True):
            self._start_background_collection()

    def _before_request(self):
        """Handle before request metrics collection."""
        request.start_time = time.time()

    def _after_request(self, response):
        """Handle after request metrics collection."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            endpoint = request.endpoint or 'unknown'
            
            # Record response time
            self.record_metric(
                name='request_duration_seconds',
                value=duration,
                tags={
                    'endpoint': endpoint,
                    'method': request.method,
                    'status_code': response.status_code
                },
                metric_type='histogram'
            )
            
            # Record request count
            self.record_metric(
                name='request_count',
                value=1,
                tags={
                    'endpoint': endpoint,
                    'method': request.method,
                    'status_code': response.status_code
                },
                metric_type='counter'
            )
        
        return response

    def _start_background_collection(self):
        """Start background metric collection."""
        from threading import Thread
        import time

        def collect_background_metrics():
            while True:
                try:
                    self.collect_system_metrics()
                    self.collect_application_metrics()
                    time.sleep(60)  # Collect every minute
                except Exception as e:
                    logger.error(f"Error collecting background metrics: {e}")

        thread = Thread(target=collect_background_metrics, daemon=True)
        thread.start()

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None,
                     metric_type: str = 'gauge', timestamp: datetime = None) -> None:
        """Record a metric value."""
        try:
            from app.models.metrics import Metric
            
            metric = Metric(
                name=name,
                value=value,
                timestamp=timestamp or datetime.utcnow(),
                tags=json.dumps(tags or {}),
                metric_type=metric_type
            )
            
            db.session.add(metric)
            db.session.commit()
            
            # Update real-time cache
            cache_key = f"metric:{name}:{json.dumps(tags or {})}"
            cache_data = {
                'value': value,
                'timestamp': metric.timestamp.isoformat(),
                'type': metric_type
            }
            cache_manager.memory_cache.set(cache_key, cache_data, timeout=300)  # Cache for 5 minutes
            
            # Emit real-time update via WebSocket
            monitoring_ns.emit_metric_update(
                metric_name=name,
                value=value,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
            db.session.rollback()

    def get_metric(self, name: str, tags: Dict[str, str] = None,
                  start_time: datetime = None, end_time: datetime = None) -> List[MetricPoint]:
        """Get metric values for a given time range."""
        try:
            from app.models.metrics import Metric
            
            query = Metric.query.filter_by(name=name)
            
            if tags:
                query = query.filter(Metric.tags.contains(json.dumps(tags)))
            
            if start_time:
                query = query.filter(Metric.timestamp >= start_time)
            
            if end_time:
                query = query.filter(Metric.timestamp <= end_time)
            
            return [
                MetricPoint(
                    name=m.name,
                    value=m.value,
                    timestamp=m.timestamp,
                    tags=json.loads(m.tags),
                    metric_type=m.metric_type
                )
                for m in query.order_by(Metric.timestamp.desc()).all()
            ]
            
        except Exception as e:
            logger.error(f"Error getting metric {name}: {e}")
            return []

    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system_cpu_percent', cpu_percent, 
                             tags={'type': 'system'})
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric('system_memory_used_bytes', memory.used,
                             tags={'type': 'system'})
            self.record_metric('system_memory_percent', memory.percent,
                             tags={'type': 'system'})
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric('system_disk_used_bytes', disk.used,
                             tags={'type': 'system'})
            self.record_metric('system_disk_percent', disk.percent,
                             tags={'type': 'system'})
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self.record_metric('system_network_bytes_sent', net_io.bytes_sent,
                             tags={'type': 'system'})
            self.record_metric('system_network_bytes_recv', net_io.bytes_recv,
                             tags={'type': 'system'})
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def collect_application_metrics(self):
        """Collect application-level metrics."""
        try:
            # Active sessions
            from flask_login import current_user
            active_sessions = len(cache_manager.memory_cache.cache._cache)
            self.record_metric('app_active_sessions', active_sessions,
                             tags={'type': 'application'})
            
            # Database connections
            if hasattr(db.engine, 'pool'):
                connections = db.engine.pool.checkedin() + db.engine.pool.checkedout()
                self.record_metric('app_db_connections', connections,
                                 tags={'type': 'application'})
            
            # Cache metrics
            cache_stats = cache_manager.get_cache_stats()
            self.record_metric('app_cache_hits', 
                             cache_stats['memory_cache']['hits'],
                             tags={'type': 'application', 'cache': 'memory'})
            self.record_metric('app_cache_misses',
                             cache_stats['memory_cache']['misses'],
                             tags={'type': 'application', 'cache': 'memory'})
            
            # Error rates (from logging handler)
            error_count = getattr(current_app, 'error_count', 0)
            self.record_metric('app_error_count', error_count,
                             tags={'type': 'application'})
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        try:
            health = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {}
            }
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            health['components']['cpu'] = {
                'status': 'healthy' if cpu_percent < 80 else 'warning',
                'value': cpu_percent
            }
            
            # Check memory usage
            memory = psutil.virtual_memory()
            health['components']['memory'] = {
                'status': 'healthy' if memory.percent < 80 else 'warning',
                'value': memory.percent
            }
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            health['components']['disk'] = {
                'status': 'healthy' if disk.percent < 80 else 'warning',
                'value': disk.percent
            }
            
            # Check database
            try:
                db.session.execute('SELECT 1')
                health['components']['database'] = {
                    'status': 'healthy',
                    'value': 100
                }
            except Exception as e:
                health['components']['database'] = {
                    'status': 'error',
                    'value': 0,
                    'error': str(e)
                }
            
            # Check cache
            try:
                cache_manager.memory_cache.set('health_check', 1)
                cache_manager.memory_cache.get('health_check')
                health['components']['cache'] = {
                    'status': 'healthy',
                    'value': 100
                }
            except Exception as e:
                health['components']['cache'] = {
                    'status': 'error',
                    'value': 0,
                    'error': str(e)
                }
            
            # Update overall status
            if any(c['status'] == 'error' for c in health['components'].values()):
                health['status'] = 'error'
            elif any(c['status'] == 'warning' for c in health['components'].values()):
                health['status'] = 'warning'
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

# Initialize metrics collector
metrics_collector = MetricsCollector()
