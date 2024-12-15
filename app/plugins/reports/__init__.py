"""Reports plugin for self-service report generation."""

from app.utils.plugin_base import PluginBase, PluginMetadata
from flask import Blueprint

class ReportsPlugin(PluginBase):
    """Reports plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="reports",
            version="1.0.0",
            description="Self-service report generation system",
            author="System",
            required_roles=["admin"],
            icon="fa-chart-bar",
            category="Admin",
            weight=100,
            permissions=[
                "reports_access",
                "reports_create",
                "reports_edit",
                "reports_delete",
                "reports_manage_db"
            ]
        )
        super().__init__(metadata)
        
        # Create blueprint with static folder
        self.blueprint = Blueprint(
            'reports',
            __name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/reports/static',
            url_prefix='/reports'
        )

    def init_app(self, app):
        """Initialize the plugin with the app."""
        super().init_app(app)

        # Import models to ensure they're registered with SQLAlchemy
        from . import models

        # Import and register template filters
        from . import template_filters
        template_filters.register_template_filters(self.blueprint)

        # Register routes from modular route files
        from . import database_routes, view_routes, data_routes
        database_routes.register_routes(self.blueprint)
        view_routes.register_routes(self.blueprint)
        data_routes.register_routes(self.blueprint)

        # Register the blueprint with the app
        app.register_blueprint(self.blueprint)

# Create plugin instance
plugin = ReportsPlugin()
