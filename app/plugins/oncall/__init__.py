"""On-call rotation management plugin."""

from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata
import logging

logger = logging.getLogger(__name__)

class OnCallPlugin(PluginBase):
    """Plugin for managing on-call rotation schedules."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="oncall",
            version="1.0.0",
            description="Manage and display on-call rotation schedules",
            author="System",
            required_roles=["admin", "demo"],
            icon="fa-calendar-alt",
            category="Operations",
            weight=100
        )
        super().__init__(metadata)
        
        # Initialize blueprint with standardized configuration
        self.blueprint = self.init_blueprint(
            template_folder='templates',
            static_folder='static'
        )
        
        # Register error handlers and other configurations
        self._register_error_handlers()
        
    def register_models(self):
        """Register models for the plugin."""
        # Import models here to avoid circular imports
        from app.plugins.oncall.models import Team, OnCallRotation
        logger.info(f"Registered models for {self.metadata.name} plugin")
        
    def register_routes(self):
        """Register routes for the plugin."""
        # Import and register routes here to avoid circular imports
        from app.plugins.oncall import routes
        routes.register_routes(self.blueprint)
        logger.info(f"Registered routes for {self.metadata.name} plugin")
        
    def register_template_filters(self):
        """Register template filters for the plugin."""
        @self.blueprint.app_template_filter('format_datetime')
        def format_datetime(value, format='%Y-%m-%d %H:%M %Z'):
            """Format datetime with timezone."""
            if value is None:
                return ""
            return value.strftime(format)
        
    def register_context_processors(self):
        """Register context processors for the plugin."""
        @self.blueprint.context_processor
        def utility_processor():
            """Add utility functions to template context."""
            def get_team_color_class(color):
                """Convert color name to Bootstrap class."""
                return f'bg-{color}'
                
            return dict(get_team_color_class=get_team_color_class)

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        super().init_app(app)
        
        # Register models
        self.register_models()
        
        # Register routes
        self.register_routes()
        
        # Register template filters
        self.register_template_filters()
        
        # Register context processors
        self.register_context_processors()
        
        # Configure logging
        if not app.debug:
            self.logger.setLevel(logging.INFO)
        
        # Log successful initialization
        logger.info(f"Initialized {self.metadata.name} plugin v{self.metadata.version}")

# Create plugin instance
plugin = OnCallPlugin()

# Make the blueprint available for import
def get_blueprint():
    """Get the plugin's blueprint."""
    return plugin.blueprint
