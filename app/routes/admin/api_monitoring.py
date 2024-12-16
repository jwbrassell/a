"""API endpoints for system monitoring."""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.extensions import cache
import psutil
from datetime import datetime, timedelta
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

def cache_key_with_user():
    """Generate a cache key that includes the user ID."""
    return f'user_{current_user.id}'

def init_monitoring_api_routes(bp):
    """Initialize monitoring API routes."""
    
    @bp.route('/monitoring/api/system-resources')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    @cache.memoize(timeout=10)  # Cache for 10 seconds per user
    def get_system_resources():
        """Get system resource usage."""
        try:
            # Get CPU and memory usage
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
            
            return jsonify({
                'success': True,
                'data': {
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
                        'upload_speed_mb': upload_speed / (1024 * 1024),  # Convert to MB/s
                        'download_speed_mb': download_speed / (1024 * 1024)  # Convert to MB/s
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            cache.delete_memoized(get_system_resources)  # Clear cache on error
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/performance')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    @cache.memoize(timeout=30)  # Cache for 30 seconds per user
    def get_performance_metrics():
        """Get application performance metrics."""
        try:
            # Get process information
            process = psutil.Process()
            process_info = {
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
            
            # Get performance data for the last hour
            now = datetime.utcnow()
            data_points = []
            
            # Cache key for performance data
            cache_key = f'perf_data_{current_user.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                data_points = cached_data
            else:
                for i in range(60):  # Last hour of data
                    timestamp = now - timedelta(minutes=i)
                    data_points.append({
                        'timestamp': timestamp.isoformat(),
                        'response_time': 100 + (i % 20),  # Mock response time in ms
                        'requests_per_second': 50 + (i % 10)
                    })
                # Cache the performance data for 5 minutes
                cache.set(cache_key, data_points, timeout=300)
            
            return jsonify({
                'success': True,
                'data': {
                    'metrics': data_points,
                    'process': process_info
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            cache.delete_memoized(get_performance_metrics)  # Clear cache on error
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/health')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    @cache.memoize(timeout=15)  # Cache for 15 seconds per user
    def get_health_status():
        """Get system health status."""
        try:
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
            
            return jsonify({
                'success': True,
                'data': {
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
                            'value': min(network_utilization, 100)  # Cap at 100%
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
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            cache.delete_memoized(get_health_status)  # Clear cache on error
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/monitoring/api/user-activity')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    @cache.memoize(timeout=60)  # Cache for 1 minute per user
    def get_user_activity():
        """Get recent user activity data."""
        try:
            # Get activity from the last 24 hours
            since = datetime.utcnow() - timedelta(hours=24)
            
            # Cache key for activity data
            cache_key = f'user_activity_{current_user.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return jsonify({
                    'success': True,
                    'data': cached_data
                })
            
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
            
            # Cache the activity data
            cache.set(cache_key, data, timeout=60)
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            cache.delete_memoized(get_user_activity)  # Clear cache on error
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    def invalidate_monitoring_cache():
        """Invalidate all monitoring-related caches."""
        cache.delete_memoized(get_system_resources)
        cache.delete_memoized(get_performance_metrics)
        cache.delete_memoized(get_health_status)
        cache.delete_memoized(get_user_activity)

    # Add cache invalidation to the blueprint
    bp.invalidate_monitoring_cache = invalidate_monitoring_cache

    return bp
