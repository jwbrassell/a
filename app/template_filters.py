"""Template filters for the Flask application."""

import json
from markupsafe import escape

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
