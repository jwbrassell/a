"""API endpoints for admin functionality."""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import User, Role, UserActivity
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

# Configure logging
logger = logging.getLogger(__name__)

def init_api_routes(bp):
    """Initialize API routes for the admin blueprint."""
    
    @bp.route('/api/user-stats')
    @login_required
    @requires_permission('admin_users_access', 'read')
    def get_user_stats():
        """Get user statistics."""
        try:
            # Get active/inactive counts
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            
            # Get new users in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
            
            # Get user activity over time
            activities = UserActivity.query.with_entities(
                func.date(UserActivity.timestamp).label('date'),
                func.count().label('count')
            ).group_by(func.date(UserActivity.timestamp)).all()
            
            activity_data = [
                [int(date.strftime('%s')) * 1000, count]
                for date, count in activities
            ]
            
            # Get role distribution
            role_counts = db.session.query(
                Role.name,
                func.count(User.id).label('count')
            ).join(
                Role.users
            ).group_by(Role.name).all()
            
            role_data = [
                {'name': name, 'y': count}
                for name, count in role_counts
            ]
            
            return jsonify({
                'active': active_users,
                'inactive': total_users - active_users,
                'new': new_users,
                'activity': activity_data,
                'roles': role_data
            })
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/users/<int:user_id>/roles')
    @login_required
    @requires_permission('admin_users_access', 'read')
    def get_user_roles(user_id):
        """Get roles for a user."""
        try:
            user = User.query.get_or_404(user_id)
            return jsonify({
                'role_ids': [role.id for role in user.roles]
            })
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return jsonify({'error': str(e)}), 500

    @bp.route('/api/users', methods=['POST'])
    @login_required
    @requires_permission('admin_users_access', 'write')
    def create_user():
        """Create a new user."""
        try:
            data = request.get_json()
            
            # Check if username or email already exists
            if User.query.filter_by(username=data['username']).first():
                return jsonify({
                    'success': False,
                    'error': 'Username already exists'
                }), 400
                
            if User.query.filter_by(email=data['email']).first():
                return jsonify({
                    'success': False,
                    'error': 'Email already exists'
                }), 400
            
            # Create user
            user = User(
                username=data['username'],
                email=data['email'],
                created_by=current_user.username
            )
            user.set_password(data['password'])
            
            # Add roles
            if 'roles' in data:
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                user.roles = roles
            
            db.session.add(user)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new user: {user.username}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
    @login_required
    @requires_permission('admin_users_access', 'write')
    def toggle_user_status(user_id):
        """Toggle user active status."""
        try:
            user = User.query.get_or_404(user_id)
            
            # Don't allow deactivating yourself
            if user.id == current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot deactivate your own account'
                }), 400
            
            user.is_active = not user.is_active
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"{'Activated' if user.is_active else 'Deactivated'} user: {user.username}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'is_active': user.is_active
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error toggling user status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
    @login_required
    @requires_permission('admin_users_access', 'write')
    def reset_user_password(user_id):
        """Reset user password."""
        try:
            user = User.query.get_or_404(user_id)
            
            # Generate random password
            new_password = User.generate_password()
            user.set_password(new_password)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Reset password for user: {user.username}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            # Send password reset email
            user.send_password_reset_email(new_password)
            
            return jsonify({
                'success': True,
                'message': 'Password reset email sent'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/users/<int:user_id>', methods=['PUT'])
    @login_required
    @requires_permission('admin_users_access', 'write')
    def update_user(user_id):
        """Update user details."""
        try:
            user = User.query.get_or_404(user_id)
            data = request.get_json()
            
            # Check if email is being changed and already exists
            if 'email' in data and data['email'] != user.email:
                if User.query.filter_by(email=data['email']).first():
                    return jsonify({
                        'success': False,
                        'error': 'Email already exists'
                    }), 400
                user.email = data['email']
            
            # Update roles if provided
            if 'roles' in data:
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                user.roles = roles
            
            # Update other fields
            for field in ['first_name', 'last_name', 'phone']:
                if field in data:
                    setattr(user, field, data[field])
            
            user.updated_by = current_user.username
            user.updated_at = datetime.utcnow()
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated user details: {user.username}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
