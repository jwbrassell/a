"""Core admin module for system management."""

from flask import Blueprint, render_template
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, 
                    url_prefix='/admin',
                    template_folder='templates',
                    static_folder='static')

def init_admin(app):
    """Initialize admin module with Flask application."""
    
    # Add admin-specific configuration
    app.config.setdefault('ADMIN_USER_ID', 1)
    app.config.setdefault('ADMIN_ITEMS_PER_PAGE', 25)
    
    # Register routes
    from app.routes.admin import routes
    from app.routes.admin.api import init_api_routes
    from app.routes.admin.api_roles import init_role_api_routes
    from app.routes.admin.api_analytics import init_analytics_api_routes
    from app.routes.admin.monitoring import init_monitoring_routes
    
    # Initialize API routes
    init_api_routes(admin_bp)
    init_role_api_routes(admin_bp)
    init_analytics_api_routes(admin_bp)
    init_monitoring_routes(admin_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors()
    
    # Register blueprint
    app.register_blueprint(admin_bp)
    
    logger.info("Initialized admin module")

def register_context_processors():
    """Register admin-specific template context processors."""
    @admin_bp.context_processor
    def inject_admin_data():
        """Inject admin-specific data into templates."""
        return {
            'admin_version': '2.0.0'  # Hardcoded since we're no longer a plugin
        }

def register_error_handlers(app):
    """Register error handlers that use main app templates."""
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
