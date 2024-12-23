"""Core admin routes."""

from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory, User
from app.extensions import db
from app.routes.admin import admin_bp as bp
from app.utils.vault_security_monitor import VaultSecurityMonitor
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, desc
from app.utils.activity_tracking import track_activity
from app.utils.analytics_service import analytics_service

# Import route modules
from . import roles  # noqa: F401
from . import icons  # noqa: F401

logger = logging.getLogger(__name__)

# Dashboard
@bp.route('/')
@login_required
@requires_permission('admin_dashboard_access', 'read')
@track_activity
def index():
    """Admin dashboard main page."""
    # Get counts for stats
    total_users = User.query.count()
    total_roles = Role.query.count()
    total_categories = NavigationCategory.query.count()
    total_routes = PageRouteMapping.query.count()
    
    # Get active users (users with activity in last 24 hours)
    active_users = db.session.query(UserActivity.username).distinct().filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # Get recent activities (last 24 hours)
    recent_activities = UserActivity.query.filter(
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).order_by(desc(UserActivity.timestamp)).all()
    
    # Get role statistics
    role_stats = {
        'total': total_roles,
        'system_roles': Role.query.filter_by(is_system_role=True).count(),
        'custom_roles': Role.query.filter_by(is_system_role=False).count(),
        'top_roles': Role.query.join(Role.users).group_by(Role.id).order_by(func.count().desc()).limit(5).all()
    }
    
    # Calculate statistics for the dashboard tiles
    stats = {
        'users': {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'new': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
        },
        'roles': {
            'total': total_roles,
            'system': role_stats['system_roles'],
            'custom': role_stats['custom_roles'],
            'with_users': Role.query.join(Role.users).group_by(Role.id).count()
        },
        'categories': {
            'total': total_categories,
            'with_routes': NavigationCategory.query.filter(
                NavigationCategory.routes.any()
            ).count(),
            'empty': total_categories - NavigationCategory.query.filter(
                NavigationCategory.routes.any()
            ).count(),
            'avg_routes': total_routes / total_categories if total_categories > 0 else 0
        },
        'routes': {
            'total': total_routes,
            'categorized': PageRouteMapping.query.filter(
                PageRouteMapping.category_id.isnot(None)
            ).count(),
            'uncategorized': PageRouteMapping.query.filter(
                PageRouteMapping.category_id.is_(None)
            ).count(),
            'restricted': PageRouteMapping.query.filter(
                PageRouteMapping.allowed_roles.any()
            ).count()
        }
    }
    
    return render_template('admin/index.html',
                         stats=stats,
                         roles=Role.query.all(),
                         categories=NavigationCategory.query.all(),
                         routes=PageRouteMapping.query.all(),
                         recent_activities=recent_activities,
                         users=User.query.all(),
                         role_stats=role_stats)

# Route Management
@bp.route('/routes')
@login_required
@requires_permission('admin_routes_access', 'read')
@track_activity
def routes():
    """List all route mappings."""
    mappings = PageRouteMapping.query.all()
    return render_template('admin/routes.html', mappings=mappings)

@bp.route('/routes/new', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_routes_access', 'write')
@track_activity
def new_route():
    """Create a new route mapping."""
    if request.method == 'POST':
        try:
            mapping = PageRouteMapping(
                route=request.form['route'],
                page_name=request.form['page_name'],
                description=request.form.get('description'),
                category_id=request.form.get('category_id'),
                icon=request.form.get('icon', 'fa-link'),
                weight=int(request.form.get('weight', 0)),
                created_by=current_user.username
            )
            db.session.add(mapping)
            db.session.commit()
            flash(f'Route "{mapping.page_name}" created successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating route: {e}")
            flash('Error creating route. Please try again.', 'danger')
    
    categories = NavigationCategory.query.all()
    return render_template('admin/route_form.html',
                         mapping=None,
                         categories=categories)

@bp.route('/routes/<int:route_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_routes_access', 'write')
@track_activity
def edit_route(route_id):
    """Edit an existing route mapping."""
    mapping = PageRouteMapping.query.get_or_404(route_id)
    
    if request.method == 'POST':
        try:
            mapping.route = request.form['route']
            mapping.page_name = request.form['page_name']
            mapping.description = request.form.get('description')
            mapping.category_id = request.form.get('category_id')
            mapping.icon = request.form.get('icon', 'fa-link')
            mapping.weight = int(request.form.get('weight', 0))
            mapping.updated_by = current_user.username
            mapping.updated_at = datetime.utcnow()
            
            # Update allowed roles
            if request.form.getlist('allowed_roles[]'):
                role_ids = [int(rid) for rid in request.form.getlist('allowed_roles[]')]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                mapping.allowed_roles = roles
            else:
                mapping.allowed_roles = []
            
            db.session.commit()
            flash(f'Route "{mapping.page_name}" updated successfully.', 'success')
            return redirect(url_for('admin.routes'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating route: {e}")
            flash('Error updating route. Please try again.', 'danger')
    
    categories = NavigationCategory.query.all()
    roles = Role.query.all()
    return render_template('admin/route_form.html',
                         mapping=mapping,
                         categories=categories,
                         roles=roles)

@bp.route('/routes/<int:route_id>/delete')
@login_required
@requires_permission('admin_routes_access', 'delete')
@track_activity
def delete_route(route_id):
    """Delete a route mapping."""
    mapping = PageRouteMapping.query.get_or_404(route_id)
    
    try:
        name = mapping.page_name
        db.session.delete(mapping)
        db.session.commit()
        flash(f'Route "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting route: {e}")
        flash('Error deleting route. Please try again.', 'danger')
    
    return redirect(url_for('admin.routes'))

@bp.route('/routes/list')
@login_required
@requires_permission('admin_routes_access', 'read')
def get_routes():
    """Get list of available routes for route mapping."""
    # Get all registered routes
    routes = []
    for rule in current_app.url_map.iter_rules():
        if not rule.endpoint.startswith('static'):
            routes.append({
                'endpoint': rule.endpoint,
                'route': rule.rule,
                'methods': list(rule.methods)
            })
    return jsonify(routes)

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
        monitor = VaultSecurityMonitor(current_app.vault)
        summary = monitor.generate_security_report()
        return render_template('admin/vault_status.html',
                             status=summary['overall_status'],
                             summary=summary)
    except Exception as e:
        logger.error(f"Failed to get Vault status: {e}")
        flash('Failed to retrieve Vault status.', 'danger')
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
