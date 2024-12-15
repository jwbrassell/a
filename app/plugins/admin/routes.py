from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory, User
from app import db
from app.plugins.admin import bp
from app.utils.vault_security_monitor import VaultMonitor
from datetime import datetime, timedelta
import logging
import re
from sqlalchemy import func
from werkzeug.routing import Map
import json
import os
from app.utils.activity_tracking import track_activity
from app.utils.analytics_service import analytics_service

logger = logging.getLogger(__name__)

# Dashboard
@bp.route('/')
@login_required
@requires_permission('admin_dashboard_access', 'read')
@track_activity
def index():
    """Admin dashboard main page."""
    # Get counts for stats
    roles = Role.query.all()
    categories = NavigationCategory.query.all()
    routes = PageRouteMapping.query.all()
    users = User.query.all()
    
    # Get recent activities (last 24 hours)
    recent_activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).all()
    
    return render_template('admin/index.html',
                         roles=roles,
                         categories=categories,
                         routes=routes,
                         recent_activities=recent_activities,
                         users=users)

# Analytics Dashboard
@bp.route('/analytics')
@login_required
@requires_permission('admin_analytics_access', 'read')
@track_activity
def analytics():
    """Business Intelligence Analytics Dashboard."""
    return render_template('admin/analytics.html')

# Vault Status
@bp.route('/vault')
@login_required
@requires_permission('admin_vault_access', 'read')
@track_activity
def vault_status():
    """View Vault server status and health."""
    try:
        monitor = VaultMonitor(current_app.vault)
        summary = monitor.get_monitoring_summary()
        return render_template('admin/vault_status.html',
                             status=summary['status'],
                             summary=summary)
    except Exception as e:
        logger.error(f"Failed to get Vault status: {e}")
        flash('Failed to retrieve Vault status.', 'danger')
        return redirect(url_for('admin.index'))

# Monitoring
@bp.route('/monitoring')
@login_required
@requires_permission('admin_monitoring_access', 'read')
@track_activity
def monitoring():
    """View system monitoring information."""
    try:
        monitor = VaultMonitor(current_app.vault)
        summary = monitor.get_monitoring_summary()
        return render_template('admin/monitoring.html',
                             status=summary['status'],
                             summary=summary)
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        flash('Failed to retrieve monitoring status.', 'danger')
        return redirect(url_for('admin.index'))

# User Management
@bp.route('/users')
@login_required
@requires_permission('admin_users_access', 'read')
@track_activity
def users():
    """List all users and manage their roles."""
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin/users.html', users=users, all_roles=all_roles)

# Role Management
@bp.route('/roles')
@login_required
@requires_permission('admin_roles_access', 'read')
@track_activity
def roles():
    """List all roles and their permissions."""
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

# Navigation Categories Management
@bp.route('/categories')
@login_required
@requires_permission('admin_categories_access', 'read')
@track_activity
def categories():
    """List all navigation categories."""
    categories = NavigationCategory.query.all()
    return render_template('admin/categories.html', categories=categories)

# Route Management
@bp.route('/routes')
@login_required
@requires_permission('admin_routes_access', 'read')
@track_activity
def routes():
    """List all route mappings."""
    mappings = PageRouteMapping.query.all()
    return render_template('admin/routes.html', mappings=mappings)

# Activity Logs
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

# Icon Management
@bp.route('/icons')
@login_required
@requires_permission('admin_icons_access', 'read')
@track_activity
def get_icons():
    """Get list of available FontAwesome icons."""
    # This is a simplified list - you might want to expand it
    icons = [
        'fa-user', 'fa-users', 'fa-cog', 'fa-wrench', 'fa-folder', 
        'fa-file', 'fa-chart-bar', 'fa-dashboard', 'fa-home',
        'fa-list', 'fa-check', 'fa-times', 'fa-plus', 'fa-minus',
        'fa-edit', 'fa-trash', 'fa-save', 'fa-search', 'fa-envelope',
        'fa-bell', 'fa-calendar', 'fa-clock', 'fa-star', 'fa-heart',
        'fa-bookmark', 'fa-print', 'fa-camera', 'fa-video', 'fa-music',
        'fa-map', 'fa-location-dot', 'fa-link', 'fa-lock', 'fa-unlock',
        'fa-key', 'fa-gear', 'fa-tools', 'fa-database', 'fa-server',
        'fa-network-wired', 'fa-cloud', 'fa-upload', 'fa-download',
        'fa-vault', 'fa-chart-line', 'fa-chart-pie', 'fa-project-diagram',
        'fa-tasks', 'fa-trophy', 'fa-dollar-sign'
    ]
    return jsonify(icons)
