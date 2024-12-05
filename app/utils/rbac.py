from functools import wraps
from flask import current_app, request, render_template, flash
from flask_login import current_user
from werkzeug.exceptions import Forbidden
from app.models import PageRouteMapping
from app import db

def check_route_access():
    """
    Check if the current user has access to the requested route based on their roles.
    
    Returns:
        bool: True if user has access, False otherwise
    """
    if not current_user.is_authenticated:
        return False
        
    # Skip checks for static files and error pages
    if request.endpoint and request.endpoint.startswith(('static', 'main.error')):
        return True
        
    try:
        # Get the route mapping for the current endpoint
        mapping = PageRouteMapping.query.filter_by(route=request.path).first()
        
        if not mapping:
            # If no mapping exists, default to requiring authentication only
            return True
            
        # Get the set of role names required for this route
        required_roles = {role.name for role in mapping.allowed_roles}
        
        if not required_roles:
            # If no roles are specified, default to requiring authentication only
            return True
            
        # Get the set of user's role names
        user_roles = {role.name for role in current_user.roles}
        
        # Check if user has any of the required roles
        return bool(required_roles & user_roles)  # Returns True if there's any intersection
        
    except Exception as e:
        current_app.logger.error(f"Error checking route access: {str(e)}")
        db.session.rollback()
        return False

def requires_roles(*role_names):
    """
    Decorator to require specific roles for accessing a route.
    
    Args:
        *role_names: Variable number of role names required for access
        
    Returns:
        function: Decorated route function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return current_app.login_manager.unauthorized()
                
            # Get the set of user's role names
            user_roles = {role.name for role in current_user.roles}
            
            # Check if user has any of the required roles
            if not set(role_names) & user_roles:
                flash('You do not have permission to access this page.', 'warning')
                return render_template('403.html'), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_accessible_routes():
    """
    Get all routes accessible to the current user based on their roles.
    
    Returns:
        list: List of PageRouteMapping objects the user has access to
    """
    if not current_user.is_authenticated:
        return []
        
    try:
        # Get all mappings ordered by weight
        mappings = PageRouteMapping.query.order_by(PageRouteMapping.weight).all()
        
        # Get the set of user's role names
        user_roles = {role.name for role in current_user.roles}
        
        # Filter mappings based on user roles
        accessible_mappings = []
        for mapping in mappings:
            mapping_roles = {role.name for role in mapping.allowed_roles}
            if not mapping_roles or mapping_roles & user_roles:
                accessible_mappings.append(mapping)
                
        return accessible_mappings
        
    except Exception as e:
        current_app.logger.error(f"Error getting accessible routes: {str(e)}")
        db.session.rollback()
        return []
