"""
Role-Based Access Control (RBAC) system for Flask application.
"""
from functools import wraps
from flask import current_app, request, render_template, flash
from flask_login import current_user
from werkzeug.exceptions import Forbidden
from app.models import PageRouteMapping
from app import db
from app.utils.route_manager import route_to_endpoint

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

    # Admin users always have access to everything
    if any(role.name == 'admin' for role in current_user.roles):
        return True
        
    try:
        # Validate the endpoint exists
        endpoint = route_to_endpoint(request.path)
        if not endpoint:
            current_app.logger.warning(f"Attempted access to non-existent route: {request.path}")
            return False
            
        # Get the route mapping for the current endpoint
        mapping = PageRouteMapping.query.filter_by(route=endpoint).first()
        
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

            # Admin users always have access
            if any(role.name == 'admin' for role in current_user.roles):
                return f(*args, **kwargs)
                
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

        # Admin users can access all routes
        if any(role.name == 'admin' for role in current_user.roles):
            return [m for m in mappings if route_to_endpoint(m.route)]
        
        # Get the set of user's role names
        user_roles = {role.name for role in current_user.roles}
        
        # Filter mappings based on user roles and route existence
        accessible_mappings = []
        for mapping in mappings:
            # Verify the route still exists
            endpoint = route_to_endpoint(mapping.route)
            if not endpoint or endpoint not in current_app.view_functions:
                current_app.logger.warning(f"Skipping invalid route in access check: {mapping.route}")
                continue
                
            # Check role access
            mapping_roles = {role.name for role in mapping.allowed_roles}
            if not mapping_roles or mapping_roles & user_roles:
                accessible_mappings.append(mapping)
                
        return accessible_mappings
        
    except Exception as e:
        current_app.logger.error(f"Error getting accessible routes: {str(e)}")
        db.session.rollback()
        return []

def cleanup_invalid_role_mappings():
    """
    Remove role mappings for routes that no longer exist.
    
    Returns:
        tuple: (number of mappings removed, list of removed routes)
    """
    try:
        removed_count = 0
        removed_routes = []
        
        # Get all route mappings
        mappings = PageRouteMapping.query.all()
        
        for mapping in mappings:
            # Check if the endpoint exists
            endpoint = route_to_endpoint(mapping.route)
            if not endpoint or endpoint not in current_app.view_functions:
                # Log the removal
                current_app.logger.info(f"Removing invalid role mapping: {mapping.route}")
                removed_routes.append(mapping.route)
                removed_count += 1
                
                # Remove the mapping
                db.session.delete(mapping)
        
        # Commit changes if any mappings were removed
        if removed_count > 0:
            db.session.commit()
            current_app.logger.info(f"Removed {removed_count} invalid role mappings")
        
        return removed_count, removed_routes
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cleaning up invalid role mappings: {str(e)}")
        return 0, []
