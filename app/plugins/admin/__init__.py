"""Admin plugin for system management."""

from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata
from app.utils.enhanced_rbac import requires_permission
import logging

# Configure logging
logger = logging.getLogger(__name__)

class AdminPlugin(PluginBase):
    """Admin plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name='admin',
            version='2.0.0',
            description='Administrative interface for managing users, roles, and system settings',
            author='System',
            required_roles=['admin'],
            icon='fas fa-cogs',
            category='System',
            weight=0  # Show first in navigation
        )
        super().__init__(metadata)
        
        # Initialize blueprint with standard configuration
        self.init_blueprint(
            template_folder='templates',
            static_folder='static'
        )
        
        # Register routes and APIs
        self.register_routes()

    def register_routes(self):
        """Register admin routes and APIs."""
        if not self.blueprint:
            raise RuntimeError("Blueprint not initialized")

        # Import and register main routes
        from app.plugins.admin import routes
        
        # Import and register API routes
        from app.plugins.admin.api import init_api_routes
        from app.plugins.admin.api_roles import init_role_api_routes
        from app.plugins.admin.api_analytics import init_analytics_api_routes
        
        # Initialize API routes
        init_api_routes(self.blueprint)
        init_role_api_routes(self.blueprint)
        init_analytics_api_routes(self.blueprint)
        
        # Import monitoring module
        from app.plugins.admin import monitoring

        @self.blueprint.context_processor
        def inject_admin_data():
            """Inject admin-specific data into templates."""
            return {
                'admin_plugin': self,
                'admin_version': self.metadata.version
            }

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        super().init_app(app)
        
        # Add admin-specific configuration
        app.config.setdefault('ADMIN_USER_ID', 1)
        app.config.setdefault('ADMIN_ITEMS_PER_PAGE', 25)
        
        # Register error handlers that use main app templates
        self.register_error_handlers(app)
        
        logger.info(f"Initialized admin plugin v{self.metadata.version}")

    def register_error_handlers(self, app):
        """Register error handlers that use main app templates."""
        @app.errorhandler(403)
        @requires_permission('admin_error_access', 'read')
        def forbidden_error(error):
            return render_template('403.html'), 403

        @app.errorhandler(404)
        @requires_permission('admin_error_access', 'read')
        def not_found_error(error):
            return render_template('404.html'), 404

        @app.errorhandler(500)
        @requires_permission('admin_error_access', 'read')
        def internal_error(error):
            return render_template('500.html'), 500

# Create plugin instance
plugin = AdminPlugin()
