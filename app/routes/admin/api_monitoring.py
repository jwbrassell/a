"""API endpoints for system monitoring."""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.extensions import db
from app.utils.cache_manager import cache_manager
from app.utils.alert_service import alert_service
from app.models.metrics import MetricAlert, Metric
from datetime import datetime, timedelta
import psutil
import logging
from app.models.activity import UserActivity
from sqlalchemy import func, extract
import time
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Cache for network speed calculation
last_net_io = None
last_net_io_time = None
# Network interface speed (100 Mbps is common minimum)
NETWORK_BASE_SPEED = 100 * 1024 * 1024  # 100 Mbps in bytes/sec

def calculate_network_speed():
    """Calculate current network speed in bytes/sec."""
    global last_net_io, last_net_io_time
    
    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    
    if last_net_io is None or last_net_io_time is None:
        last_net_io = current_net_io
        last_net_io_time = current_time
        return 0, 0
    
    time_delta = current_time - last_net_io_time
    if time_delta == 0:
        return 0, 0
        
    # Calculate speeds
    upload_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_delta
    download_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_delta
    
    # Update last values
    last_net_io = current_net_io
    last_net_io_time = current_time
    
    return upload_speed, download_speed

def get_network_status(upload_speed, download_speed):
    """Calculate network status based on actual usage."""
    # Calculate total utilization as percentage of base speed
    total_speed = upload_speed + download_speed
    utilization = (total_speed / NETWORK_BASE_SPEED) * 100
    
    # Return status based on utilization
    if utilization < 70:
        return 'success', utilization
    elif utilization < 85:
        return 'warning', utilization
    else:
        return 'error', utilization

def get_historical_metrics(metric_name: str, hours: int = 24) -> list:
    """Get historical metrics for the specified name and time range."""
    since = datetime.utcnow() - timedelta(hours=hours)
    metrics = Metric.query.filter(
        Metric.name == metric_name,
        Metric.timestamp >= since
    ).order_by(Metric.timestamp.asc()).all()
    
    logger.debug(f"Retrieved {len(metrics)} historical metrics for {metric_name}")
    return [{'timestamp': m.timestamp.isoformat(), 'value': m.value} for m in metrics]

def init_monitoring_api_routes(bp):
    """Initialize monitoring API routes."""
    
    @bp.route('/monitoring/api/system-resources')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def get_system_resources():
        """Get system resource usage with historical data."""
        try:
            logger.debug("Fetching system resources...")
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Get network speeds
            upload_speed, download_speed = calculate_network_speed()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get per-CPU usage
            cpu_per_core = psutil.cpu_percent(percpu=True)
            
            # Get memory details
            swap = psutil.swap_memory()
            
            # Get historical data for the last 24 hours
            historical_data = {
                'cpu': get_historical_metrics('system_cpu_percent'),
                'memory': get_historical_metrics('system_memory_percent'),
                'disk': get_historical_metrics('system_disk_percent'),
                'network_sent': get_historical_metrics('system_network_bytes_sent'),
                'network_recv': get_historical_metrics('system_network_bytes_recv')
            }
            
            logger.debug("Successfully retrieved system resources and historical data")
            
            return jsonify({
                'success': True,
                'data': {
                    'current': {
                        'cpu': {
                            'percent': cpu_percent,
                            'per_core': cpu_per_core,
                            'count': psutil.cpu_count(),
                            'count_logical': psutil.cpu_count(logical=True)
                        },
                        'memory': {
                            'total': memory.total,
                            'available': memory.available,
                            'used': memory.used,
                            'free': memory.free,
                            'percent': memory.percent,
                            'swap_total': swap.total,
                            'swap_used': swap.used,
                            'swap_free': swap.free,
                            'swap_percent': swap.percent
                        },
                        'disk': {
                            'total': disk.total,
                            'used': disk.used,
                            'free': disk.free,
                            'percent': disk.percent
                        },
                        'network': {
                            'upload_speed': upload_speed,
                            'download_speed': download_speed,
                            'upload_speed_mb': upload_speed / (1024 * 1024),
                            'download_speed_mb': download_speed / (1024 * 1024)
                        }
                    },
                    'historical': historical_data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/alerts', methods=['GET'])
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def get_alerts():
        """Get all metric alerts."""
        try:
            alerts = MetricAlert.query.all()
            return jsonify({
                'success': True,
                'data': [alert.to_dict() for alert in alerts]
            })
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/alerts', methods=['POST'])
    @login_required
    @requires_permission('admin_monitoring_access', 'write')
    def create_alert():
        """Create a new metric alert."""
        try:
            data = request.get_json()
            alert = alert_service.create_alert(
                name=data['name'],
                metric_name=data['metric_name'],
                condition=data['condition'],
                threshold=float(data['threshold']),
                duration=int(data['duration']),
                tags=data.get('tags')
            )
            return jsonify({
                'success': True,
                'data': alert.to_dict()
            })
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/alerts/<int:alert_id>', methods=['PUT'])
    @login_required
    @requires_permission('admin_monitoring_access', 'write')
    def update_alert(alert_id):
        """Update an existing metric alert."""
        try:
            data = request.get_json()
            alert = alert_service.update_alert(
                alert_id,
                **{k: v for k, v in data.items() if k in [
                    'name', 'metric_name', 'condition', 'threshold',
                    'duration', 'tags', 'enabled'
                ]}
            )
            return jsonify({
                'success': True,
                'data': alert.to_dict()
            })
        except Exception as e:
            logger.error(f"Error updating alert: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/alerts/<int:alert_id>', methods=['DELETE'])
    @login_required
    @requires_permission('admin_monitoring_access', 'write')
    def delete_alert(alert_id):
        """Delete a metric alert."""
        try:
            success = alert_service.delete_alert(alert_id)
            return jsonify({
                'success': success
            })
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/performance')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def get_performance_metrics():
        """Get application performance metrics with historical data."""
        try:
            logger.debug("Fetching performance metrics...")
            # Get process information
            process = psutil.Process()
            process_info = {
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
            
            # Get historical response time data
            historical_data = get_historical_metrics('request_duration_seconds')
            
            logger.debug("Successfully retrieved performance metrics")
            
            return jsonify({
                'success': True,
                'data': {
                    'current': process_info,
                    'historical': historical_data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/health')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def get_health_status():
        """Get system health status with historical data."""
        try:
            logger.debug("Fetching health status...")
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network status
            upload_speed, download_speed = calculate_network_speed()
            network_status, network_utilization = get_network_status(upload_speed, download_speed)
            
            # Get load average
            load_avg = psutil.getloadavg()
            
            # Get system uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            def get_status(value):
                if value < 70:
                    return 'success'
                elif value < 85:
                    return 'warning'
                else:
                    return 'error'
            
            # Get historical health data
            historical_data = {
                'cpu': get_historical_metrics('system_cpu_percent'),
                'memory': get_historical_metrics('system_memory_percent'),
                'disk': get_historical_metrics('system_disk_percent')
            }
            
            logger.debug("Successfully retrieved health status")
            
            return jsonify({
                'success': True,
                'data': {
                    'current': {
                        'components': {
                            'cpu': {
                                'status': get_status(cpu_percent),
                                'value': cpu_percent
                            },
                            'memory': {
                                'status': get_status(memory.percent),
                                'value': memory.percent
                            },
                            'disk': {
                                'status': get_status(disk.percent),
                                'value': disk.percent
                            },
                            'network': {
                                'status': network_status,
                                'value': min(network_utilization, 100)
                            }
                        },
                        'system': {
                            'load_average': {
                                '1min': load_avg[0],
                                '5min': load_avg[1],
                                '15min': load_avg[2]
                            },
                            'uptime': {
                                'days': uptime.days,
                                'hours': uptime.seconds // 3600,
                                'minutes': (uptime.seconds % 3600) // 60
                            }
                        }
                    },
                    'historical': historical_data
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/user-activity')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def get_user_activity():
        """Get recent user activity data."""
        try:
            logger.debug("Fetching user activity...")
            # Get activity from the last 24 hours
            since = datetime.utcnow() - timedelta(hours=24)
            
            # Query recent activities
            activities = UserActivity.query.filter(
                UserActivity.timestamp >= since
            ).order_by(UserActivity.timestamp.desc()).limit(100).all()
            
            # Get activity counts by hour using SQLite-compatible date functions
            hourly_counts = UserActivity.query.with_entities(
                func.strftime('%Y-%m-%d %H:00:00', UserActivity.timestamp).label('hour'),
                func.count().label('count')
            ).filter(
                UserActivity.timestamp >= since
            ).group_by('hour').order_by('hour').all()
            
            data = {
                'recent_actions': [{
                    'timestamp': activity.timestamp.isoformat(),
                    'user_id': activity.user_id,
                    'action': activity.activity,
                    'details': activity.username
                } for activity in activities],
                'hourly_activity': [{
                    'hour': hour,
                    'count': count
                } for hour, count in hourly_counts]
            }
            
            logger.debug("Successfully retrieved user activity")
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
