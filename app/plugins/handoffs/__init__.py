"""Handoffs plugin for managing shift handovers."""

from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata
import logging

logger = logging.getLogger(__name__)

class HandoffsPlugin(PluginBase):
    """Plugin for managing shift handovers between teams."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="handoffs",
            version="1.0.0",
            description="Manage shift handovers between teams with comprehensive tracking and metrics",
            author="System",
            required_roles=["user"],
            icon="fa-exchange-alt",
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
        from app.plugins.handoffs.models import Handoff, HandoffShift
        logger.info(f"Registered models for {self.metadata.name} plugin")
        
    def register_routes(self):
        """Register routes for the plugin."""
        # Import and register routes here to avoid circular imports
        from app.plugins.handoffs import routes
        routes.register_routes(self.blueprint)
        logger.info(f"Registered routes for {self.metadata.name} plugin")
        
    def register_template_filters(self):
        """Register template filters for the plugin."""
        @self.blueprint.app_template_filter('format_priority')
        def format_priority(priority):
            """Format priority with appropriate color class."""
            colors = {
                'high': 'danger',
                'medium': 'warning',
                'low': 'info'
            }
            return colors.get(priority, 'secondary')
        
    def register_context_processors(self):
        """Register context processors for the plugin."""
        @self.blueprint.context_processor
        def utility_processor():
            """Add utility functions to template context."""
            def get_shift_name(shift_id):
                """Get readable shift name."""
                shifts = {
                    '1st': 'First Shift',
                    '2nd': 'Second Shift',
                    '3rd': 'Third Shift'
                }
                return shifts.get(shift_id, shift_id)
                
            return dict(get_shift_name=get_shift_name)

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
        
        # Initialize plugin
        with app.app_context():
            # Register permissions
            from app.utils.enhanced_rbac import register_permission
            permissions = [
                'handoffs_view',
                'handoffs_create',
                'handoffs_edit',
                'handoffs_delete'
            ]
            for permission in permissions:
                register_permission(
                    permission,
                    f"Permission for {permission}"
                )
        
        # Log successful initialization
        logger.info(f"Initialized {self.metadata.name} plugin v{self.metadata.version}")

# Create plugin instance
plugin = HandoffsPlugin()

# Make the blueprint available for import
bp = plugin.blueprint
