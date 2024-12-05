from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.models import Role, PageRouteMapping, UserActivity, NavigationCategory, User
from app import db
from app.plugins.admin import bp
from datetime import datetime, timedelta
import logging
import re
from sqlalchemy import func
from werkzeug.routing import Map

logger = logging.getLogger(__name__)

# Dashboard
@bp.route('/')
@login_required
@requires_roles('admin')
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

# User Management
@bp.route('/users')
@login_required
@requires_roles('admin')
def users():
    """List all users and manage their roles."""
    users = User.query.all()
    all_roles = Role.query.all()
    return render_template('admin/users.html', users=users, all_roles=all_roles)

@bp.route('/users/<int:id>/roles', methods=['POST'])
@login_required
@requires_roles('admin')
def update_user_roles(id):
    """Update roles for a user."""
    user = User.query.get_or_404(id)
    try:
        # Get selected role IDs from form
        role_ids = request.form.getlist('roles')
        
        # Get role objects
        new_roles = Role.query.filter(Role.id.in_(role_ids)).all() if role_ids else []
        
        # Update user's roles
        old_roles = set(role.name for role in user.roles)
        user.roles = new_roles
        new_roles_set = set(role.name for role in new_roles)
        
        # Create activity log
        added_roles = new_roles_set - old_roles
        removed_roles = old_roles - new_roles_set
        activity_desc = []
        if added_roles:
            activity_desc.append(f"Added roles: {', '.join(added_roles)}")
        if removed_roles:
            activity_desc.append(f"Removed roles: {', '.join(removed_roles)}")
        
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"Updated roles for user {user.username}. {' '.join(activity_desc)}"
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Roles updated successfully for {user.username}.',
            'roles': [{'id': role.id, 'name': role.name} for role in new_roles]
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user roles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error updating user roles.'
        }), 500

# Rest of the file remains unchanged...
