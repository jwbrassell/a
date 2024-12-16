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
        
        # Register error handlers and other configurations
        self._register_error_handlers()
        
    def register_models(self):
        """Register models for the plugin."""
        # Import models here to avoid circular imports
        from app.plugins.projects.models import (
            Project, Task, Todo, Comment, History,
            ProjectStatus, ProjectPriority
        )
        logger.info(f"Registered models for {self.metadata.name} plugin")
        
    def register_routes(self):
        """Register routes for the plugin."""
        # Import routes here to avoid circular imports
        from app.plugins.projects import (
            main_routes, project_routes, task_routes,
            subtask_routes, comment_routes, management_routes,
            priority_routes, status_routes
        )
        
        # Register route modules with blueprint
        main_routes.register_routes(self.blueprint)
        project_routes.register_routes(self.blueprint)
        task_routes.register_routes(self.blueprint)
        subtask_routes.register_routes(self.blueprint)
        comment_routes.register_routes(self.blueprint)
        management_routes.register_routes(self.blueprint)
        priority_routes.register_routes(self.blueprint)
        status_routes.register_routes(self.blueprint)
        
        logger.info(f"Registered routes for {self.metadata.name} plugin")
        
    def register_template_filters(self):
        """Register template filters for the plugin."""
        from app.plugins.projects.models import ProjectStatus, ProjectPriority
        
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
        from app.plugins.projects.utils import can_edit_project
        
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
                from app.plugins.projects.utils import init_default_configurations
                init_default_configurations(app)
        
        # Initialize caching
        if app.config.get('ENABLE_CACHING'):
            from app.plugins.projects.utils.caching import init_cache
            init_cache(app)
        
        # Initialize monitoring if enabled
        if app.config.get('ENABLE_QUERY_TRACKING'):
            from app.plugins.projects.utils.monitoring import init_monitoring
            init_monitoring(app)
        
        # Register CLI commands
        from app.plugins.projects.utils import register_commands
        register_commands(app)
        
        # Log successful initialization
        logger.info(f"Initialized {self.metadata.name} plugin v{self.metadata.version}")

# Create plugin instance
plugin = ProjectsPlugin()

# Make the blueprint available for import
bp = plugin.blueprint
