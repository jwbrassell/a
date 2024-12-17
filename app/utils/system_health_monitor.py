"""System health monitoring functionality."""

import psutil
from typing import Dict, Any
from datetime import datetime
import logging
from app.models.metrics import Metric
from app.utils.alert_service import alert_service
from app import db

logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitor and collect system health metrics."""
    
    # Define default thresholds
    DEFAULT_THRESHOLDS = {
        'cpu_usage': {
            'warning': 80.0,  # 80% CPU usage
            'critical': 90.0  # 90% CPU usage
        },
        'memory_usage': {
            'warning': 85.0,  # 85% memory usage
            'critical': 95.0  # 95% memory usage
        },
        'disk_usage': {
            'warning': 85.0,  # 85% disk usage
            'critical': 95.0  # 95% disk usage
        }
    }
    
    @staticmethod
    def collect_metrics() -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network metrics (basic)
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.utcnow(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'core_count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'usage_percent': memory_percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'usage_percent': disk_percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    @classmethod
    def store_metrics(cls) -> bool:
        """Collect and store system metrics."""
        try:
            metrics = cls.collect_metrics()
            if not metrics:
                return False
            
            # Store CPU metrics
            cpu_metric = Metric(
                name='system.cpu.usage',
                value=metrics['cpu']['usage_percent'],
                tags={'cores': metrics['cpu']['core_count']},
                metric_type='gauge'  # Add metric_type
            )
            db.session.add(cpu_metric)
            
            # Store memory metrics
            memory_metric = Metric(
                name='system.memory.usage',
                value=metrics['memory']['usage_percent'],
                tags={
                    'total': metrics['memory']['total'],
                    'available': metrics['memory']['available']
                },
                metric_type='gauge'  # Add metric_type
            )
            db.session.add(memory_metric)
            
            # Store disk metrics
            disk_metric = Metric(
                name='system.disk.usage',
                value=metrics['disk']['usage_percent'],
                tags={
                    'total': metrics['disk']['total'],
                    'free': metrics['disk']['free']
                },
                metric_type='gauge'  # Add metric_type
            )
            db.session.add(disk_metric)
            
            db.session.commit()
            
            # Check alerts after storing metrics
            cls.check_alerts(metrics)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error storing system metrics: {e}")
            return False
    
    @classmethod
    def check_alerts(cls, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts if needed."""
        try:
            # Check CPU usage
            if metrics['cpu']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['cpu_usage']['critical']:
                alert_service.create_alert(
                    name='Critical CPU Usage',
                    metric_name='system.cpu.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['cpu_usage']['critical'],
                    duration=300,  # 5 minutes
                    tags={'severity': 'critical'}
                )
            elif metrics['cpu']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['cpu_usage']['warning']:
                alert_service.create_alert(
                    name='High CPU Usage',
                    metric_name='system.cpu.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['cpu_usage']['warning'],
                    duration=300,
                    tags={'severity': 'warning'}
                )
            
            # Check memory usage
            if metrics['memory']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['memory_usage']['critical']:
                alert_service.create_alert(
                    name='Critical Memory Usage',
                    metric_name='system.memory.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['memory_usage']['critical'],
                    duration=300,
                    tags={'severity': 'critical'}
                )
            elif metrics['memory']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['memory_usage']['warning']:
                alert_service.create_alert(
                    name='High Memory Usage',
                    metric_name='system.memory.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['memory_usage']['warning'],
                    duration=300,
                    tags={'severity': 'warning'}
                )
            
            # Check disk usage
            if metrics['disk']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['disk_usage']['critical']:
                alert_service.create_alert(
                    name='Critical Disk Usage',
                    metric_name='system.disk.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['disk_usage']['critical'],
                    duration=3600,  # 1 hour for disk alerts
                    tags={'severity': 'critical'}
                )
            elif metrics['disk']['usage_percent'] >= cls.DEFAULT_THRESHOLDS['disk_usage']['warning']:
                alert_service.create_alert(
                    name='High Disk Usage',
                    metric_name='system.disk.usage',
                    condition='>',
                    threshold=cls.DEFAULT_THRESHOLDS['disk_usage']['warning'],
                    duration=3600,
                    tags={'severity': 'warning'}
                )
                
        except Exception as e:
            logger.error(f"Error checking system health alerts: {e}")
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Get current system status with threshold evaluations."""
        try:
            metrics = SystemHealthMonitor.collect_metrics()
            
            status = {
                'timestamp': metrics['timestamp'].isoformat(),
                'status': 'healthy',  # Default status
                'components': {
                    'cpu': {
                        'status': 'healthy',
                        'value': metrics['cpu']['usage_percent'],
                        'message': 'CPU usage is normal'
                    },
                    'memory': {
                        'status': 'healthy',
                        'value': metrics['memory']['usage_percent'],
                        'message': 'Memory usage is normal'
                    },
                    'disk': {
                        'status': 'healthy',
                        'value': metrics['disk']['usage_percent'],
                        'message': 'Disk usage is normal'
                    }
                }
            }
            
            # Evaluate CPU status
            if metrics['cpu']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['cpu_usage']['critical']:
                status['components']['cpu'].update({
                    'status': 'critical',
                    'message': 'Critical CPU usage detected'
                })
                status['status'] = 'critical'
            elif metrics['cpu']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['cpu_usage']['warning']:
                status['components']['cpu'].update({
                    'status': 'warning',
                    'message': 'High CPU usage detected'
                })
                status['status'] = 'warning'
            
            # Evaluate memory status
            if metrics['memory']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['memory_usage']['critical']:
                status['components']['memory'].update({
                    'status': 'critical',
                    'message': 'Critical memory usage detected'
                })
                status['status'] = 'critical'
            elif metrics['memory']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['memory_usage']['warning']:
                status['components']['memory'].update({
                    'status': 'warning',
                    'message': 'High memory usage detected'
                })
                status['status'] = 'warning'
            
            # Evaluate disk status
            if metrics['disk']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['disk_usage']['critical']:
                status['components']['disk'].update({
                    'status': 'critical',
                    'message': 'Critical disk usage detected'
                })
                status['status'] = 'critical'
            elif metrics['disk']['usage_percent'] >= SystemHealthMonitor.DEFAULT_THRESHOLDS['disk_usage']['warning']:
                status['components']['disk'].update({
                    'status': 'warning',
                    'message': 'High disk usage detected'
                })
                status['status'] = 'warning'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'message': f'Error collecting system status: {str(e)}'
            }

# Initialize system health monitor
system_monitor = SystemHealthMonitor()
