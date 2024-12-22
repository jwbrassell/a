"""Monitoring and analytics routes for admin module."""

from flask import render_template, flash, redirect, url_for, current_app
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission
from app.routes.admin import admin_bp as bp
from app.utils.activity_tracking import track_activity
from app.models import UserActivity
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@bp.route('/analytics')
@login_required
@requires_permission('admin_analytics_access', 'read')
@track_activity
def analytics():
    """Business Intelligence Analytics Dashboard."""
    return render_template('admin/analytics.html')

@bp.route('/logs')
@login_required
@requires_permission('admin_logs_access', 'read')
@track_activity
def logs():
    """View system activity logs."""
    # Get activities from the last 7 days by default
    activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).order_by(UserActivity.timestamp.desc()).all()
    return render_template('admin/logs.html', activities=activities)

@bp.route('/monitoring')
@login_required
@requires_permission('admin_monitoring_access', 'read')
@track_activity
def monitoring():
    """System monitoring dashboard."""
    return render_template('admin/monitoring/index.html')
