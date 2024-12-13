"""
Routes for the admin monitoring dashboard
"""
from flask import Blueprint, render_template, jsonify
from app.utils.rbac import requires_roles
from .metrics import MetricsCollector

# Create blueprint without url_prefix since it's registered under admin blueprint
bp = Blueprint('monitoring', __name__)

@bp.route('/monitoring')
@requires_roles('admin')
def monitoring_dashboard():
    """Main monitoring dashboard"""
    return render_template('admin/monitoring/dashboard.html')

@bp.route('/monitoring/system')
@requires_roles('admin')
def system_metrics():
    """Get system metrics"""
    try:
        current = MetricsCollector.collect_system_metrics()
        history = MetricsCollector.get_system_metrics_history()
        
        return jsonify({
            'current': [metric.to_dict() for metric in (current or [])],
            'history': [metric.to_dict() for metric in (history or [])]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'current': [],
            'history': []
        }), 500

@bp.route('/monitoring/application')
@requires_roles('admin')
def application_metrics():
    """Get application metrics"""
    try:
        current = MetricsCollector.collect_application_metrics()
        history = MetricsCollector.get_application_metrics_history()
        
        return jsonify({
            'current': [metric.to_dict() for metric in (current or [])],
            'history': [metric.to_dict() for metric in (history or [])]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'current': [],
            'history': []
        }), 500

@bp.route('/monitoring/features')
@requires_roles('admin')
def feature_metrics():
    """Get feature usage metrics"""
    try:
        daily = MetricsCollector.get_feature_metrics(days=1)
        weekly = MetricsCollector.get_feature_metrics(days=7)
        monthly = MetricsCollector.get_feature_metrics(days=30)
        trends = MetricsCollector.get_feature_usage_trends()
        
        return jsonify({
            'daily': [{'feature': f.feature, 'plugin': f.plugin, 
                      'count': f.usage_count, 'avg_duration': float(f.avg_duration or 0)} 
                     for f in (daily or [])],
            'weekly': [{'feature': f.feature, 'plugin': f.plugin, 
                       'count': f.usage_count, 'avg_duration': float(f.avg_duration or 0)} 
                      for f in (weekly or [])],
            'monthly': [{'feature': f.feature, 'plugin': f.plugin, 
                        'count': f.usage_count, 'avg_duration': float(f.avg_duration or 0)} 
                       for f in (monthly or [])],
            'trends': [{'feature': t.feature, 'plugin': t.plugin, 
                       'date': t.date.isoformat(), 'count': t.usage_count, 
                       'avg_duration': float(t.avg_duration or 0)} 
                      for t in (trends or [])]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'daily': [],
            'weekly': [],
            'monthly': [],
            'trends': []
        }), 500

@bp.route('/monitoring/resources')
@requires_roles('admin')
def resource_metrics():
    """Get resource utilization metrics"""
    try:
        daily = MetricsCollector.get_resource_utilization(days=1)
        weekly = MetricsCollector.get_resource_utilization(days=7)
        monthly = MetricsCollector.get_resource_utilization(days=30)
        
        return jsonify({
            'daily': [{'type': r.resource_type, 'category': r.category, 
                      'value': float(r.total_value or 0)} for r in (daily or [])],
            'weekly': [{'type': r.resource_type, 'category': r.category, 
                       'value': float(r.total_value or 0)} for r in (weekly or [])],
            'monthly': [{'type': r.resource_type, 'category': r.category, 
                        'value': float(r.total_value or 0)} for r in (monthly or [])]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'daily': [],
            'weekly': [],
            'monthly': []
        }), 500

@bp.route('/monitoring/users')
@requires_roles('admin')
def user_metrics():
    """Get user activity metrics"""
    try:
        history = MetricsCollector.get_user_metrics_history()
        
        return jsonify({
            'history': [metric.to_dict() for metric in (history or [])]
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'history': []
        }), 500
