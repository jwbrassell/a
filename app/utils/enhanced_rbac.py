"""Enhanced Role-Based Access Control (RBAC) system for Flask application."""
from functools import wraps
from flask import current_app, request, render_template, abort
from flask_login import current_user
import logging
from app.extensions import db
from app.models.permission import Permission
from app.models.permissions import Action, RoutePermission
from app.utils.route_manager import route_to_endpoint

logger = logging.getLogger(__name__)

class PermissionDenied(Exception):
    """Custom exception for permission denied errors."""
    def __init__(self, message="Permission denied", status_code=403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def get_response(self):
        """Return the HTTP response for this error."""
        return render_template('403.html'), self.status_code

def has_permission(permission_name, action_name=None):
    """
    Check if the current user has access to the specified permission and action.
    Similar to check_permission_access but can be used directly in templates and code.
    
    Args:
        permission_name: Name of the permission to check
        action_name: Optional action name to check
    
    Returns:
        bool: True if user has access, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    try:
        # Admin users always have access
        if any(role.name == 'Administrator' for role in current_user.roles):
            return True
        
        # Get the permission
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            logger.warning(f"Permission not found: {permission_name}")
            return False
        
        # Check if user has any role with this permission
        user_has_permission = False
        for role in current_user.roles:
            if permission in role.permissions:
                user_has_permission = True
                break
            # Check parent roles if they exist
            parent = role
            while parent.parent_id:
                parent = parent.parent
                if permission in parent.permissions:
                    user_has_permission = True
                    break
            if user_has_permission:
                break
        
        if not user_has_permission:
            return False
        
        # If action is specified, check action permission
        if action_name:
            action = Action.query.filter_by(
                name=action_name,
                method=request.method if request else 'GET'
            ).first()
            
            if not action or action not in permission.actions:
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking permission access: {str(e)}")
        return False

def register_permission(name, description=None, actions=None, roles=None, category=None):
    """
    Register a new permission with optional actions and roles.
    
    Args:
        name: Name of the permission
        description: Optional description of the permission
        actions: Optional list of action names to associate
        roles: Optional list of role names to grant permission to
    
    Returns:
        Permission object if successful, None if failed
    """
    try:
        # Check if permission already exists
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            permission = Permission(
                name=name,
                description=description or f"Permission for {name}",
                category=category or name.split('_')[0],  # Default to first part of name
                created_by='system'
            )
            db.session.add(permission)
            
            # Add actions if specified
            if actions:
                for action_name in actions:
                    action = Action.query.filter_by(name=action_name).first()
                    if action and action not in permission.actions:
                        permission.actions.append(action)
            
            # Add roles if specified
            if roles:
                from app.models import Role
                for role_name in roles:
                    role = Role.query.filter_by(name=role_name).first()
                    if role and permission not in role.permissions:
                        role.permissions.append(permission)
            
            db.session.commit()
            logger.info(f"Successfully registered permission: {name}")
            return permission
        else:
            logger.info(f"Permission already exists: {name}")
            return permission
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering permission: {str(e)}")
        return None

def init_default_actions():
    """Initialize default actions if they don't exist."""
    default_actions = [
        ('read', 'GET', 'Read access'),
        ('write', 'POST', 'Create access'),
        ('update', 'PUT', 'Update access'),
        ('delete', 'DELETE', 'Delete access'),
        ('list', 'GET', 'List access'),
    ]
    
    try:
        for name, method, description in default_actions:
            if not Action.query.filter_by(name=name, method=method).first():
                action = Action(
                    name=name,
                    method=method,
                    description=description,
                    created_by='system'
                )
                db.session.add(action)
        
        db.session.commit()
        logger.info("Default actions initialized successfully")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing default actions: {str(e)}")
        raise

def check_permission_access(permission_name, action_name=None):
    """
    Check if the current user has access to the specified permission and action.
    
    Args:
        permission_name: Name of the permission to check
        action_name: Optional action name to check (will be matched with request method)
    
    Returns:
        bool: True if user has access, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    try:
        # Admin users always have access
        if any(role.name == 'Administrator' for role in current_user.roles):
            return True
        
        # Get the permission
        permission = Permission.query.filter_by(name=permission_name).first()
        if not permission:
            logger.warning(f"Permission not found: {permission_name}")
            return False
        
        # Check if user has any role with this permission
        user_has_permission = False
        for role in current_user.roles:
            if permission in role.permissions:
                user_has_permission = True
                break
            # Check parent roles if they exist
            parent = role
            while parent.parent_id:
                parent = parent.parent
                if permission in parent.permissions:
                    user_has_permission = True
                    break
            if user_has_permission:
                break
        
        if not user_has_permission:
            return False
        
        # If action is specified, check action permission
        if action_name:
            action = Action.query.filter_by(
                name=action_name,
                method=request.method
            ).first()
            
            if not action or action not in permission.actions:
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking permission access: {str(e)}")
        return False

def requires_permission(permission_name, *actions):
    """
    Decorator to require specific permission and optional actions for a route.
    
    Args:
        permission_name: Name of the permission required
        *actions: Optional action names required (e.g., 'read', 'write')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            
            # Admin users always have access
            if any(role.name == 'Administrator' for role in current_user.roles):
                return f(*args, **kwargs)
            
            # For each action, check permission
            for action in actions:
                if not check_permission_access(permission_name, action):
                    logger.warning(
                        f"Permission denied: {permission_name} with action {action} "
                        f"for user {current_user.username}"
                    )
                    raise PermissionDenied(
                        f"Permission denied: {permission_name} with action {action}"
                    )
            
            # If no actions specified, just check the permission
            if not actions and not check_permission_access(permission_name):
                logger.warning(
                    f"Permission denied: {permission_name} "
                    f"for user {current_user.username}"
                )
                raise PermissionDenied(f"Permission denied: {permission_name}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_permissions():
    """Get all permissions available to the current user."""
    if not current_user.is_authenticated:
        return []
    
    try:
        permissions = set()
        
        # Admin users have all permissions
        if any(role.name == 'Administrator' for role in current_user.roles):
            return Permission.query.all()
        
        # Get permissions from user's roles and their parent roles
        for role in current_user.roles:
            permissions.update(role.permissions)
            
            # Check parent roles
            parent = role
            while parent.parent_id:
                parent = parent.parent
                permissions.update(parent.permissions)
        
        return list(permissions)
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        return []

def setup_role_hierarchy(role_hierarchy):
    """
    Set up role hierarchy based on provided mapping.
    
    Args:
        role_hierarchy: Dict mapping role names to their parent role names
        Example: {'user': 'manager', 'manager': 'admin'}
    """
    from app.models import Role
    
    try:
        for role_name, parent_name in role_hierarchy.items():
            role = Role.query.filter_by(name=role_name).first()
            parent = Role.query.filter_by(name=parent_name).first()
            
            if role and parent:
                role.parent_id = parent.id
            else:
                logger.warning(f"Role not found: {role_name} or {parent_name}")
        
        db.session.commit()
        logger.info("Successfully set up role hierarchy")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting up role hierarchy: {str(e)}")
        return False
