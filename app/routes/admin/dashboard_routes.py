"""Dashboard routes for admin module."""

from flask import render_template
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory, User
from app.extensions import db
from app.routes.admin import admin_bp as bp
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.utils.activity_tracking import track_activity

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
