"""Weblinks plugin for managing and organizing web links."""

from app.utils.plugin_base import PluginBase, PluginMetadata
from flask import Blueprint

class WeblinksPlugin(PluginBase):
    """Weblinks plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="Web Links",
            version="1.0.0",
            description="Manage and organize web links with categories, tags, and notes",
            author="System",
            required_roles=["user"],  # At least user role required
            icon="fa-link",
            category="Tools",
            weight=50,
            permissions=[
                "weblinks_access",      # Basic access to view links
                "weblinks_manage",      # Create, edit, delete links/categories/tags
                "weblinks_import_export"  # Import/export functionality
            ]
        )
        super().__init__(metadata)
        
        # Create blueprint with static folder
        self.blueprint = Blueprint(
            'weblinks',
            __name__,
            template_folder='templates',
            static_folder='static',
            url_prefix='/weblinks'
        )

    def init_app(self, app):
        """Initialize the plugin with the app."""
        super().init_app(app)

        # Import models to ensure they're registered with SQLAlchemy
        from . import models

        # Register routes from modular route files
        from . import (
            link_routes,
            category_routes,
            tag_routes,
            import_export_routes
        )

        # Initialize plugin
        with app.app_context():
            # Register permissions
            from app.utils.enhanced_rbac import register_permission
            for permission in self.metadata.permissions:
                register_permission(
                    permission,
                    f"Permission for {permission}"
                )

            # Register all route modules
            link_routes.register_routes(self.blueprint)
            category_routes.register_routes(self.blueprint)
            tag_routes.register_routes(self.blueprint)
            import_export_routes.register_routes(self.blueprint)

            # Register the blueprint with the app
            app.register_blueprint(self.blueprint)

# Create plugin instance
plugin = WeblinksPlugin()

# Make the blueprint available for import
bp = plugin.blueprint
