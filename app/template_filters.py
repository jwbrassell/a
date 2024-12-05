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
        return route.replace('/', '.')

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

    @app.template_filter('route_exists')
    def route_exists(endpoint):
        """Check if a route exists in the application."""
        try:
            return endpoint in current_app.view_functions
        except:
            return False
