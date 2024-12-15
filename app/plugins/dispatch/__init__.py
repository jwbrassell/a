"""Dispatch plugin for managing and tracking dispatch requests."""

from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata

# Create blueprint first so it can be imported by routes
bp = Blueprint('dispatch', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/dispatch')

class DispatchPlugin(PluginBase):
    """Dispatch plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="Dispatch Tool",
            version="1.0.0",
            description="Manage and track dispatch requests with email notifications",
            author="System",
            required_roles=["user", "admin"],
            icon="fa-paper-plane",
            category="Tools",
            weight=100
        )
        super().__init__(metadata)
        
        # Use existing blueprint
        self.blueprint = bp

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        super().init_app(app)
        
        # Import routes after app initialization
        from app.plugins.dispatch import routes
        
        # Add dispatch-specific configuration
        app.config.setdefault('DISPATCH_ITEMS_PER_PAGE', 20)
        
        # Configure email settings if not set
        app.config.setdefault('MAIL_SERVER', 'localhost')
        app.config.setdefault('MAIL_PORT', 25)
        app.config.setdefault('MAIL_USE_TLS', False)
        app.config.setdefault('MAIL_USERNAME', None)
        app.config.setdefault('MAIL_PASSWORD', None)
        app.config.setdefault('MAIL_DEFAULT_SENDER', 'dispatch@example.com')
        
        # Register error handlers
        self.register_error_handlers(app)
        
        # Register dispatch routes
        from .utils.register_routes import register_dispatch_routes
        with app.app_context():
            register_dispatch_routes()

    def register_error_handlers(self, app):
        """Register error handlers."""
        @app.errorhandler(500)
        def internal_error(error):
            """Handle internal server errors."""
            app.logger.error(f'Server Error: {error}')
            return 'Internal Server Error', 500

# Create plugin instance
plugin = DispatchPlugin()
