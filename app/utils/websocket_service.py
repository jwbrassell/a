"""WebSocket service for real-time monitoring."""

from flask_socketio import SocketIO, emit
from flask import current_app
from flask_login import current_user
from functools import wraps
from app.utils.enhanced_rbac import check_permission_access
import json
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio = SocketIO()

def requires_socket_permission(permission):
    """Decorator to check socket permissions."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return False
            if not check_permission_access(permission, 'read'):
                return False
            return f(*args, **kwargs)
        return wrapped
    return decorator

class MonitoringNamespace:
    """Namespace for monitoring-related WebSocket events."""
    
    def __init__(self):
        self.clients = set()
        
    def init_handlers(self):
        """Initialize WebSocket event handlers."""
        
        @socketio.on('connect', namespace='/monitoring')
        @requires_socket_permission('admin_monitoring_access')
        def handle_connect():
            """Handle client connection."""
            try:
                client_id = current_user.id
                self.clients.add(client_id)
                logger.info(f"Client {client_id} connected to monitoring namespace")
                # Send initial system status
                self.emit_system_status(client_id)
            except Exception as e:
                logger.error(f"Error in handle_connect: {e}")
        
        @socketio.on('disconnect', namespace='/monitoring')
        def handle_disconnect():
            """Handle client disconnection."""
            try:
                client_id = current_user.id
                self.clients.discard(client_id)
                logger.info(f"Client {client_id} disconnected from monitoring namespace")
            except Exception as e:
                logger.error(f"Error in handle_disconnect: {e}")
        
        @socketio.on('subscribe_metrics', namespace='/monitoring')
        @requires_socket_permission('admin_monitoring_access')
        def handle_subscribe_metrics(data):
            """Handle metric subscription request."""
            try:
                metric_names = data.get('metrics', [])
                client_id = current_user.id
                logger.info(f"Client {client_id} subscribed to metrics: {metric_names}")
                # Store subscription preferences (could be extended to database)
                current_app.config.setdefault('metric_subscriptions', {})
                current_app.config['metric_subscriptions'][client_id] = metric_names
            except Exception as e:
                logger.error(f"Error in handle_subscribe_metrics: {e}")
    
    def emit_system_status(self, client_id=None):
        """Emit current system status."""
        try:
            from app.utils.metrics_collector import metrics_collector
            health = metrics_collector.get_system_health()
            
            if client_id:
                # Emit to specific client
                emit('system_status', health, namespace='/monitoring', room=client_id)
            else:
                # Broadcast to all clients
                emit('system_status', health, namespace='/monitoring', broadcast=True)
        except Exception as e:
            logger.error(f"Error emitting system status: {e}")
    
    def emit_metric_update(self, metric_name, value, tags=None):
        """Emit metric update to subscribed clients."""
        try:
            update = {
                'name': metric_name,
                'value': value,
                'timestamp': datetime.utcnow().isoformat(),
                'tags': tags or {}
            }
            
            # Get subscriptions
            subscriptions = current_app.config.get('metric_subscriptions', {})
            
            # Emit to subscribed clients
            for client_id, metrics in subscriptions.items():
                if metric_name in metrics and client_id in self.clients:
                    emit('metric_update', update, namespace='/monitoring', room=client_id)
        except Exception as e:
            logger.error(f"Error emitting metric update: {e}")
    
    def emit_alert(self, alert_data):
        """Emit alert to all connected clients."""
        try:
            emit('alert', alert_data, namespace='/monitoring', broadcast=True)
        except Exception as e:
            logger.error(f"Error emitting alert: {e}")

# Initialize monitoring namespace
monitoring_ns = MonitoringNamespace()

def init_websocket(app):
    """Initialize WebSocket service with Flask app."""
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")
    monitoring_ns.init_handlers()
    return socketio
