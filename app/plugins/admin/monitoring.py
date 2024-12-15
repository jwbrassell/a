"""Admin monitoring module for system and application metrics."""

from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required
from app.utils.metrics_collector import metrics_collector
from app.models.metrics import Metric, MetricAlert, MetricDashboard
from app.extensions import db
from datetime import datetime, timedelta
import logging
from typing import Dict, Any
import json
from app.utils.vault_security_monitor import VaultSecurityMonitor

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@bp.route('/')
@login_required
def index():
    """Monitoring dashboard index."""
    try:
        # Get system health
        health = metrics_collector.get_system_health()
        
        # Get recent metrics
        recent_metrics = Metric.query.order_by(
            Metric.timestamp.desc()
        ).limit(100).all()
        
        # Get active alerts
        alerts = MetricAlert.query.filter_by(enabled=True).all()
        
        # Get custom dashboards
        dashboards = MetricDashboard.query.all()
        
        return render_template(
            'admin/monitoring/index.html',
            health=health,
            recent_metrics=recent_metrics,
            alerts=alerts,
            dashboards=dashboards
        )
    except Exception as e:
        logger.error(f"Error in monitoring dashboard: {e}")
        return render_template('error.html', error=str(e)), 500

@bp.route('/api/health')
@login_required
def get_health():
    """Get system health status."""
    try:
        health = metrics_collector.get_system_health()
        return jsonify(health)
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/metrics')
@login_required
def get_metrics():
    """Get metrics data."""
    try:
        metric_name = request.args.get('name')
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        tags = json.loads(request.args.get('tags', '{}'))
        
        if start_time:
            start_time = datetime.fromisoformat(start_time)
        if end_time:
            end_time = datetime.fromisoformat(end_time)
        
        metrics = Metric.get_metrics_by_name(
            name=metric_name,
            start_time=start_time,
            end_time=end_time,
            tags=tags
        )
        
        return jsonify([m.to_dict() for m in metrics])
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/metrics/stats')
@login_required
def get_metric_stats():
    """Get metric statistics."""
    try:
        metric_name = request.args.get('name')
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        tags = json.loads(request.args.get('tags', '{}'))
        
        if start_time:
            start_time = datetime.fromisoformat(start_time)
        if end_time:
            end_time = datetime.fromisoformat(end_time)
        
        stats = Metric.get_metric_statistics(
            name=metric_name,
            start_time=start_time,
            end_time=end_time,
            tags=tags
        )
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting metric statistics: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/alerts', methods=['GET', 'POST'])
@login_required
def manage_alerts():
    """Manage metric alerts."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            alert = MetricAlert(
                name=data['name'],
                metric_name=data['metric_name'],
                condition=data['condition'],
                threshold=float(data['threshold']),
                duration=int(data['duration']),
                tags=data.get('tags', {}),
                enabled=data.get('enabled', True)
            )
            db.session.add(alert)
            db.session.commit()
            return jsonify(alert.to_dict())
        
        alerts = MetricAlert.query.all()
        return jsonify([a.to_dict() for a in alerts])
    except Exception as e:
        logger.error(f"Error managing alerts: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/dashboards', methods=['GET', 'POST'])
@login_required
def manage_dashboards():
    """Manage metric dashboards."""
    try:
        if request.method == 'POST':
            data = request.get_json()
            dashboard = MetricDashboard(
                name=data['name'],
                description=data.get('description', ''),
                layout=data['layout'],
                created_by_id=current_app.config['ADMIN_USER_ID']
            )
            db.session.add(dashboard)
            db.session.commit()
            return jsonify(dashboard.to_dict())
        
        dashboards = MetricDashboard.query.all()
        return jsonify([d.to_dict() for d in dashboards])
    except Exception as e:
        logger.error(f"Error managing dashboards: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/performance')
@login_required
def get_performance_metrics():
    """Get application performance metrics."""
    try:
        # Get cache performance
        cache_stats = current_app.cache_manager.get_cache_stats()
        
        # Get database performance
        db_stats = {
            'connections': db.engine.pool.checkedin() + db.engine.pool.checkedout()
            if hasattr(db.engine, 'pool') else 0
        }
        
        # Get request performance metrics
        request_metrics = Metric.query.filter(
            Metric.name == 'request_duration_seconds',
            Metric.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        performance = {
            'cache': cache_stats,
            'database': db_stats,
            'requests': [m.to_dict() for m in request_metrics]
        }
        
        return jsonify(performance)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/user-activity')
@login_required
def get_user_activity():
    """Get user activity metrics."""
    try:
        # Get active sessions
        active_sessions = len(current_app.cache_manager.memory_cache.cache._cache)
        
        # Get recent user actions
        user_metrics = Metric.query.filter(
            Metric.tags.contains('"type":"user_action"'),
            Metric.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(Metric.timestamp.desc()).all()
        
        activity = {
            'active_sessions': active_sessions,
            'recent_actions': [m.to_dict() for m in user_metrics]
        }
        
        return jsonify(activity)
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/system-resources')
@login_required
def get_system_resources():
    """Get system resource utilization."""
    try:
        # Get system metrics for the last hour
        system_metrics = Metric.query.filter(
            Metric.tags.contains('"type":"system"'),
            Metric.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(Metric.timestamp.desc()).all()
        
        # Group metrics by name
        resources = {}
        for metric in system_metrics:
            name = metric.name
            if name not in resources:
                resources[name] = []
            resources[name].append(metric.to_dict())
        
        return jsonify(resources)
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/vault-security')
@login_required
def get_vault_security():
    """Get Vault security status."""
    try:
        monitor = VaultSecurityMonitor()
        report = monitor.generate_security_report()
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error getting Vault security status: {e}")
        return jsonify({'error': str(e)}), 500
