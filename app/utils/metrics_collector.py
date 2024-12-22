"""Metrics collection utility for application monitoring."""

import psutil
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from flask import current_app
from app.extensions import db, cache_manager
from app.utils.websocket_service import monitoring_ns
from dataclasses import dataclass
import json
import threading

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
        self._collection_thread = None
        self._stop_collection = False
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        app.logger.info("Initializing MetricsCollector...")
        
        # Register before_request handler
        app.before_request(self._before_request)
        
        # Register after_request handler
        app.after_request(self._after_request)
        
        # Start background collection if enabled
        if app.config.get('METRICS_ENABLED', True):
            self._start_background_collection()
            app.logger.info("Started background metrics collection")

    def _before_request(self):
        """Handle before request metrics collection."""
        from flask import request
        request.start_time = time.time()

    def _after_request(self, response):
        """Handle after request metrics collection."""
        from flask import request
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

    def _collect_metrics(self):
        """Background metrics collection function."""
        logger.info("Starting metrics collection thread")
        while not self._stop_collection:
            try:
                with self.app.app_context():
                    logger.debug("Collecting metrics...")
                    self.collect_system_metrics()
                    self.collect_application_metrics()
                    logger.debug("Metrics collection completed")
            except Exception as e:
                logger.error(f"Error in metrics collection thread: {e}")
            time.sleep(60)  # Collect every minute

    def _start_background_collection(self):
        """Start background metric collection."""
        if self._collection_thread is None or not self._collection_thread.is_alive():
            self._stop_collection = False
            self._collection_thread = threading.Thread(target=self._collect_metrics, daemon=True)
            self._collection_thread.start()
            logger.info("Background metrics collection thread started")

    def stop_collection(self):
        """Stop background metric collection."""
        logger.info("Stopping metrics collection...")
        self._stop_collection = True
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
            logger.info("Metrics collection stopped")

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
            
            logger.debug(f"Recorded metric: {name}={value}")
            
            # Update real-time cache
            cache_key = f"metric:{name}:{json.dumps(tags or {})}"
            cache_data = {
                'value': value,
                'timestamp': metric.timestamp.isoformat(),
                'type': metric_type
            }
            if hasattr(cache_manager, 'memory_cache'):
                cache_manager.memory_cache.set(cache_key, cache_data, timeout=300)
            
            # Emit real-time update via WebSocket if available
            if hasattr(monitoring_ns, 'emit_metric_update'):
                monitoring_ns.emit_metric_update(
                    metric_name=name,
                    value=value,
                    tags=tags
                )
            
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
            db.session.rollback()

    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system_cpu_percent', cpu_percent, 
                             tags={'type': 'system'})
            logger.debug(f"Collected CPU metrics: {cpu_percent}%")
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_metric('system_memory_used_bytes', memory.used,
                             tags={'type': 'system'})
            self.record_metric('system_memory_percent', memory.percent,
                             tags={'type': 'system'})
            logger.debug(f"Collected memory metrics: {memory.percent}%")
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_metric('system_disk_used_bytes', disk.used,
                             tags={'type': 'system'})
            self.record_metric('system_disk_percent', disk.percent,
                             tags={'type': 'system'})
            logger.debug(f"Collected disk metrics: {disk.percent}%")
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self.record_metric('system_network_bytes_sent', net_io.bytes_sent,
                             tags={'type': 'system'})
            self.record_metric('system_network_bytes_recv', net_io.bytes_recv,
                             tags={'type': 'system'})
            logger.debug("Collected network metrics")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def collect_application_metrics(self):
        """Collect application-level metrics."""
        try:
            # Active sessions
            if hasattr(cache_manager, 'memory_cache'):
                active_sessions = len(cache_manager.memory_cache.cache._cache)
                self.record_metric('app_active_sessions', active_sessions,
                                 tags={'type': 'application'})
                logger.debug(f"Collected active sessions: {active_sessions}")
            
            # Database connections
            if hasattr(db, 'engine') and hasattr(db.engine, 'pool'):
                connections = db.engine.pool.checkedin() + db.engine.pool.checkedout()
                self.record_metric('app_db_connections', connections,
                                 tags={'type': 'application'})
                logger.debug(f"Collected DB connections: {connections}")
            
            # Cache metrics
            if hasattr(cache_manager, 'get_cache_stats'):
                cache_stats = cache_manager.get_cache_stats()
                if 'memory_cache' in cache_stats:
                    self.record_metric('app_cache_hits', 
                                     cache_stats['memory_cache']['hits'],
                                     tags={'type': 'application', 'cache': 'memory'})
                    self.record_metric('app_cache_misses',
                                     cache_stats['memory_cache']['misses'],
                                     tags={'type': 'application', 'cache': 'memory'})
                    logger.debug("Collected cache metrics")
            
            # Error rates (from logging handler)
            error_count = getattr(current_app, 'error_count', 0)
            self.record_metric('app_error_count', error_count,
                             tags={'type': 'application'})
            logger.debug(f"Collected error count: {error_count}")
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")

# Initialize metrics collector
metrics_collector = MetricsCollector()
