"""User API endpoints for admin module."""
from flask import jsonify, request
from flask_login import login_required
from app.utils.enhanced_rbac import requires_permission
from app.routes.admin import admin_bp as bp
from app.models import User, Role
from app.utils.activity_tracking import track_activity
from datetime import datetime, timedelta
from sqlalchemy import func, text

@bp.route('/api/users')
@login_required
@requires_permission('admin_users_access', 'read')
def get_users():
    """Get list of users with optional filtering."""
    # Get query parameters
    search = request.args.get('search', '').strip().lower()
    role_id = request.args.get('role_id')
    exclude_role_id = request.args.get('exclude_role_id')
    limit = request.args.get('limit', type=int)
    
    # Start with base query
    query = User.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.name.ilike(f'%{search}%'))
        )
    
    # Filter by role if provided
    if role_id:
        query = query.filter(User.roles.any(id=role_id))
    
    # Exclude users with specific role if provided
    if exclude_role_id:
        query = query.filter(~User.roles.any(id=exclude_role_id))
    
    # Apply limit if provided
    if limit:
        query = query.limit(limit)
    
    # Execute query and format results
    users = query.all()
    
    return jsonify({
        'results': [{
            'id': user.id,
            'text': f'{user.username} ({user.name})' if user.name else user.username,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'avatar_url': user.get_avatar_url(),
            'roles': [{'id': role.id, 'name': role.name} for role in user.roles]
        } for user in users],
        'total': len(users)
    })

@bp.route('/api/users/<int:user_id>')
@login_required
@requires_permission('admin_users_access', 'read')
def get_user(user_id):
    """Get detailed information about a specific user."""
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'avatar_url': user.get_avatar_url(),
        'roles': [{
            'id': role.id,
            'name': role.name,
            'description': role.description
        } for role in user.roles],
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'is_active': user.is_active
    })

@bp.route('/api/users/search')
@login_required
@requires_permission('admin_users_access', 'read')
def search_users():
    """Search users for Select2 dropdown integration."""
    # Get search parameters
    term = request.args.get('term', '').strip().lower()
    page = request.args.get('page', type=int, default=1)
    
    # Items per page
    per_page = 10
    
    # Build query
    query = User.query
    
    # Apply search filter if term provided
    if term:
        query = query.filter(
            (User.username.ilike(f'%{term}%')) |
            (User.email.ilike(f'%{term}%')) |
            (User.name.ilike(f'%{term}%'))
        )
    
    # Get paginated results
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Format for Select2
    return jsonify({
        'results': [{
            'id': user.id,
            'text': f'{user.username} ({user.name})' if user.name else user.username,
            'avatar_url': user.get_avatar_url(),
            'email': user.email
        } for user in users],
        'pagination': {
            'more': total > (page * per_page)
        }
    })

@bp.route('/api/users/validate-username')
@login_required
@requires_permission('admin_users_access', 'read')
def validate_username():
    """Check if a username is available."""
    username = request.args.get('username', '').strip()
    user_id = request.args.get('user_id')  # For excluding current user when editing
    
    if not username:
        return jsonify({
            'valid': False,
            'message': 'Username is required'
        })
    
    # Check if username exists
    existing_user = User.query.filter(User.username == username).first()
    if existing_user and str(existing_user.id) != user_id:
        return jsonify({
            'valid': False,
            'message': 'This username is already taken'
        })
    
    return jsonify({
        'valid': True,
        'message': 'Username is available'
    })

@bp.route('/api/users/validate-email')
@login_required
@requires_permission('admin_users_access', 'read')
def validate_email():
    """Check if an email is available."""
    email = request.args.get('email', '').strip()
    user_id = request.args.get('user_id')  # For excluding current user when editing
    
    if not email:
        return jsonify({
            'valid': False,
            'message': 'Email is required'
        })
    
    # Check if email exists
    existing_user = User.query.filter(User.email == email).first()
    if existing_user and str(existing_user.id) != user_id:
        return jsonify({
            'valid': False,
            'message': 'This email is already registered'
        })
    
    return jsonify({
        'valid': True,
        'message': 'Email is available'
    })

@bp.route('/api/users/dashboard/activity')
@login_required
@requires_permission('admin_users_access', 'read')
def get_dashboard_activity():
    """Get hourly user activity for the last 24 hours."""
    # Get timestamp for 24 hours ago
    day_ago = datetime.utcnow() - timedelta(days=1)
    
    # Query user activity by hour using SQLite's strftime
    hourly_activity = (
        User.query
        .with_entities(
            func.strftime('%Y-%m-%d %H:00:00', User.last_login).label('hour'),
            func.count().label('count')
        )
        .filter(User.last_login >= day_ago)
        .group_by(func.strftime('%Y-%m-%d %H:00:00', User.last_login))
        .order_by(text('hour'))
        .all()
    )
    
    return jsonify({
        'success': True,
        'data': {
            'hourly_activity': [
                {
                    'hour': h.hour,
                    'count': h.count
                }
                for h in hourly_activity
            ]
        }
    })

@bp.route('/api/users/dashboard/stats')
@login_required
@requires_permission('admin_users_access', 'read')
def get_dashboard_stats():
    """Get user statistics including role distribution."""
    # Get total users
    total_users = User.query.count()
    
    # Get active users
    active_users = User.query.filter_by(is_active=True).count()
    
    # Get new users in last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_users = User.query.filter(User.created_at >= month_ago).count()
    
    # Get inactive users
    inactive_users = User.query.filter_by(is_active=False).count()
    
    # Get role distribution
    role_counts = (
        User.query
        .join(User.roles)
        .with_entities(Role.name, func.count(User.id).label('count'))
        .group_by(Role.name)
        .all()
    )
    
    return jsonify({
        'success': True,
        'data': {
            'total_users': total_users,
            'active_users': active_users,
            'new_users': new_users,
            'inactive_users': inactive_users,
            'role_distribution': [
                {'role': r.name, 'count': r.count}
                for r in role_counts
            ]
        }
    })
