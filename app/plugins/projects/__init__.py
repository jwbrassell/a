"""Projects plugin for managing project workflows."""

from flask import Blueprint
from app.utils.plugin_base import PluginBase, PluginMetadata
import logging
from logging.handlers import RotatingFileHandler
import os

logger = logging.getLogger(__name__)

class ProjectsPlugin(PluginBase):
    """Plugin for project management and tracking."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="projects",
            version="1.0.0",
            description="Project management and tracking",
            author="System",
            required_roles=["admin", "user"],
            icon="fa-project-diagram",
            category="main",
            weight=10
        )
        super().__init__(metadata)
        
        # Initialize blueprint with standardized configuration
        self.blueprint = self.init_blueprint(
            template_folder='templates',
            static_folder='static'
        )
        
        # Import routes after blueprint creation to avoid circular imports
        from app.plugins.projects import (
            main_routes, project_routes, task_routes,
            subtask_routes, comment_routes, management_routes,
            priority_routes, status_routes
        )
        
        # Register error handlers and other configurations
        self._register_error_handlers()
        
    def register_models(self):
        """Register models for the plugin."""
        from app.plugins.projects.models import (
            Project, Task, Todo, Comment, History,
            ProjectStatus, ProjectPriority
        )
        logger.info(f"Registered models for {self.metadata.name} plugin")
        
    def register_routes(self):
        """Register routes for the plugin."""
        # Routes are automatically registered via blueprint
        # Additional route registration if needed can be done here
        logger.info(f"Registered routes for {self.metadata.name} plugin")
        
    def register_template_filters(self):
        """Register template filters for the plugin."""
        from .plugin import route_to_endpoint
        
        @self.blueprint.app_template_filter('route_to_endpoint')
        def _route_to_endpoint(route):
            """Convert route name to endpoint name."""
            return route_to_endpoint(route)
        
        @self.blueprint.app_template_filter('format_status')
        def format_status(status):
            """Format status with appropriate color class."""
            if not status:
                return 'secondary'
            status_obj = ProjectStatus.query.filter_by(name=status).first()
            return status_obj.color if status_obj else 'secondary'
        
        @self.blueprint.app_template_filter('format_priority')
        def format_priority(priority):
            """Format priority with appropriate color class."""
            if not priority:
                return 'secondary'
            priority_obj = ProjectPriority.query.filter_by(name=priority).first()
            return priority_obj.color if priority_obj else 'secondary'
        
    def register_context_processors(self):
        """Register context processors for the plugin."""
        from .plugin import can_edit_project
        
        @self.blueprint.context_processor
        def utility_processor():
            """Add utility functions to template context."""
            return dict(can_edit_project=can_edit_project)

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        super().init_app(app)
        
        # Setup logging
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                'logs/projects.log',
                maxBytes=1024 * 1024,
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
        
        # Register models
        self.register_models()
        
        # Register routes
        self.register_routes()
        
        # Register template filters
        self.register_template_filters()
        
        # Register context processors
        self.register_context_processors()
        
        # Initialize default configurations
        if not app.testing:
            with app.app_context():
                from .plugin import init_default_configurations
                init_default_configurations(app)
        
        # Initialize caching
        if app.config.get('ENABLE_CACHING'):
            from .utils.caching import init_cache
            init_cache(app)
        
        # Initialize monitoring if enabled
        if app.config.get('ENABLE_QUERY_TRACKING'):
            from .utils.monitoring import init_monitoring
            init_monitoring(app)
        
        # Register CLI commands
        from .plugin import register_commands
        register_commands(app)
        
        # Log successful initialization
        logger.info(f"Initialized {self.metadata.name} plugin v{self.metadata.version}")

# Create plugin instance
plugin = ProjectsPlugin()

# Create blueprint reference for compatibility
bp = plugin.blueprint

# Import models after plugin creation to avoid circular imports
from . import models
