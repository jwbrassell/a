"""System monitoring routes."""

from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission
import psutil
import logging

# Configure logging
logger = logging.getLogger(__name__)

def init_monitoring_routes(bp):
    """Initialize monitoring routes."""
    
    @bp.route('/monitoring')
    @login_required
    @requires_permission('admin_monitoring_access', 'read')
    def monitoring():
        """View system monitoring information."""
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            def get_status(value):
                if value < 70:
                    return 'success'
                elif value < 85:
                    return 'warning'
                else:
                    return 'error'
            
            # Initialize health data
            health = {
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
                        'status': 'success',  # Default to success for network
                        'value': 100
                    }
                }
            }
            
            # Initial alerts for demonstration
            alerts = [
                {
                    'id': 1,
                    'name': 'High CPU Usage',
                    'metric_name': 'system_cpu_percent',
                    'condition': '>',
                    'threshold': 90,
                    'enabled': True,
                    'last_triggered': None
                },
                {
                    'id': 2,
                    'name': 'Low Disk Space',
                    'metric_name': 'system_disk_percent',
                    'condition': '>',
                    'threshold': 85,
                    'enabled': True,
                    'last_triggered': None
                }
            ]
            
            # The template will fetch real-time data from the API endpoints
            return render_template('admin/monitoring/index.html',
                                health=health,
                                alerts=alerts)
        except Exception as e:
            logger.error(f"Failed to get monitoring status: {e}")
            flash('Failed to retrieve monitoring status.', 'danger')
            return redirect(url_for('admin.index'))

    return bp
