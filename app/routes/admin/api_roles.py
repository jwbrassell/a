"""API endpoints for role management."""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.models import Role, User, Permission, UserActivity
from app.extensions import db
from datetime import datetime
import logging
from sqlalchemy import func
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

def init_role_api_routes(bp):
    """Initialize role management API routes."""
    
    @bp.route('/api/roles')
    @login_required
    @requires_permission('admin_roles_access', 'read')
    def get_roles():
        """Get all roles with their statistics."""
        try:
            roles = Role.query.all()
            return jsonify({
                'success': True,
                'roles': [role.to_dict() for role in roles]
            })
        except Exception as e:
            logger.error(f"Error getting roles: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>')
    @login_required
    @requires_permission('admin_roles_access', 'read')
    def get_role(role_id):
        """Get role details."""
        try:
            role = Role.query.get_or_404(role_id)
            return jsonify(role.to_dict())
        except Exception as e:
            logger.error(f"Error getting role {role_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles', methods=['POST'])
    @login_required
    @requires_permission('admin_roles_access', 'write')
    def create_role():
        """Create a new role."""
        try:
            data = request.get_json()
            
            # Check if role name already exists
            if Role.query.filter_by(name=data['name']).first():
                return jsonify({
                    'success': False,
                    'error': 'Role name already exists'
                }), 400
            
            role = Role(
                name=data['name'],
                icon=data.get('icon', 'fas fa-user-tag'),
                notes=data.get('notes'),
                created_by=current_user.username
            )
            
            db.session.add(role)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created new role: {role.name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'role': role.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>', methods=['PUT'])
    @login_required
    @requires_permission('admin_roles_access', 'write')
    def update_role(role_id):
        """Update role details."""
        try:
            role = Role.query.get_or_404(role_id)
            data = request.get_json()
            
            # Check if role name is being changed and already exists
            if data['name'] != role.name and Role.query.filter_by(name=data['name']).first():
                return jsonify({
                    'success': False,
                    'error': 'Role name already exists'
                }), 400
            
            role.name = data['name']
            role.icon = data.get('icon', role.icon)
            role.notes = data.get('notes', role.notes)
            role.updated_by = current_user.username
            role.updated_at = datetime.utcnow()
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated role: {role.name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'role': role.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>', methods=['DELETE'])
    @login_required
    @requires_permission('admin_roles_access', 'delete')
    def delete_role(role_id):
        """Delete a role."""
        try:
            role = Role.query.get_or_404(role_id)
            
            # Don't allow deleting system roles
            if role.is_system_role:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete system roles'
                }), 400
            
            role_name = role.name
            db.session.delete(role)
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Deleted role: {role_name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Role {role_name} deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting role: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>/permissions')
    @login_required
    @requires_permission('admin_roles_access', 'read')
    def get_role_permissions(role_id):
        """Get permissions for a role."""
        try:
            role = Role.query.get_or_404(role_id)
            
            # Get all permissions grouped by category
            all_permissions = Permission.query.all()
            permissions_by_group = defaultdict(list)
            
            for perm in all_permissions:
                group = perm.name.split('_')[0]  # Group by prefix
                permissions_by_group[group].append({
                    'id': perm.id,
                    'name': perm.name,
                    'granted': perm in role.permissions
                })
            
            return jsonify({
                'success': True,
                'permissions': dict(permissions_by_group)
            })
            
        except Exception as e:
            logger.error(f"Error getting role permissions: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>/permissions', methods=['PUT'])
    @login_required
    @requires_permission('admin_roles_access', 'write')
    def update_role_permissions(role_id):
        """Update permissions for a role."""
        try:
            role = Role.query.get_or_404(role_id)
            data = request.get_json()
            
            # Get permissions from IDs
            new_permissions = Permission.query.filter(
                Permission.id.in_(data['permissions'])
            ).all()
            
            # Update role permissions
            role.permissions = new_permissions
            
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Updated permissions for role: {role.name}"
            )
            db.session.add(activity)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Permissions updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating role permissions: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>/users')
    @login_required
    @requires_permission('admin_roles_access', 'read')
    def get_role_users(role_id):
        """Get users in a role."""
        try:
            role = Role.query.get_or_404(role_id)
            return jsonify({
                'success': True,
                'users': [user.to_dict() for user in role.users]
            })
        except Exception as e:
            logger.error(f"Error getting role users: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/roles/<int:role_id>/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @requires_permission('admin_roles_access', 'write')
    def remove_user_from_role(role_id, user_id):
        """Remove a user from a role."""
        try:
            role = Role.query.get_or_404(role_id)
            user = User.query.get_or_404(user_id)
            
            if role in user.roles:
                user.roles.remove(role)
                
                # Log activity
                activity = UserActivity(
                    user_id=current_user.id,
                    username=current_user.username,
                    activity=f"Removed user {user.username} from role {role.name}"
                )
                db.session.add(activity)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'User removed from role {role.name}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'User is not in this role'
                }), 400
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing user from role: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/permissions/count')
    @login_required
    @requires_permission('admin_roles_access', 'read')
    def get_permission_count():
        """Get total number of permissions."""
        try:
            count = Permission.query.count()
            return jsonify({
                'success': True,
                'count': count
            })
        except Exception as e:
            logger.error(f"Error getting permission count: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
