"""Admin module initialization."""
from flask import Blueprint, render_template
from werkzeug.exceptions import Forbidden

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
bp = admin_bp  # Alias for consistency

def init_admin(app):
    """Initialize admin module."""
    # Import routes
    from . import dashboard_routes  # noqa: F401
    from . import route_management  # noqa: F401
    from . import monitoring_routes  # noqa: F401
    from . import user_management  # noqa: F401
    from . import role_management  # noqa: F401
    from . import icons  # noqa: F401
    from . import api_analytics  # noqa: F401
    from . import api_monitoring  # noqa: F401
    from . import api_users  # noqa: F401
    
    # Initialize monitoring API routes
    from .api_monitoring import init_monitoring_api_routes
    init_monitoring_api_routes(admin_bp)
    
    # Register the blueprint
    app.register_blueprint(admin_bp)

# Register error handlers
@admin_bp.errorhandler(Forbidden)
def handle_forbidden(error):
    """Handle forbidden errors."""
    return render_template('403.html'), 403

@admin_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@admin_bp.errorhandler(500)
def handle_server_error(error):
    """Handle 500 errors."""
    return render_template('500.html'), 500
