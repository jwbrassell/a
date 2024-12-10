"""Template filters for the Flask application."""

import json
from markupsafe import escape
from flask import current_app

def init_app(app):
    """Initialize template filters.
    
    Args:
        app: Flask application instance
    """
    @app.template_filter('route_to_endpoint')
    def route_to_endpoint(route):
        """Convert route to endpoint format."""
        # If route already contains dots and no slashes, assume it's already an endpoint
        if '.' in route and '/' not in route:
            return route
            
        # Remove leading slash if present
        if route.startswith('/'):
            route = route[1:]
            
        # Convert slashes to dots
        parts = route.split('/')
        
        # Handle special cases for blueprint routes
        if len(parts) >= 2:
            # If first part is a known blueprint, keep it as prefix
            if parts[0] in ['admin', 'dispatch', 'profile', 'hello', 'documents', 'oncall']:
                return f"{parts[0]}.{'.'.join(parts[1:])}"
        
        # Default case: just join with dots
        return '.'.join(parts)

    @app.template_filter('escapejs')
    def escapejs(val):
        """Escape strings for JavaScript."""
        if val is None:
            return ''
        return json.dumps(str(val))[1:-1]  # Remove quotes added by json.dumps

    @app.template_filter('datetime')
    def format_datetime(value):
        """Format datetime objects."""
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')

    @app.template_filter('date')
    def format_date(value):
        """Format date objects."""
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')

    @app.template_filter('route_exists')
    def route_exists(endpoint):
        """Check if a route exists in the application."""
        try:
            return endpoint in current_app.view_functions
        except:
            return False
