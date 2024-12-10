"""Template filters for the Flask application."""

import json
from markupsafe import escape
from flask import current_app
from app.utils.route_manager import route_to_endpoint as convert_route

def init_app(app):
    """Initialize template filters.
    
    Args:
        app: Flask application instance
    """
    @app.template_filter('route_to_endpoint')
    def route_to_endpoint(route):
        """Convert route to endpoint format."""
        return convert_route(route)

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
    def route_exists(route):
        """Check if a route exists in the application.
        
        Args:
            route: Route path or endpoint name
            
        Returns:
            bool: True if route exists and is registered, False otherwise
        """
        try:
            # Convert route to endpoint format
            endpoint = convert_route(route)
            if not endpoint:
                return False
                
            # Check if endpoint exists in view functions
            return endpoint in current_app.view_functions
        except Exception as e:
            current_app.logger.warning(f"Error checking route existence for {route}: {str(e)}")
            return False
