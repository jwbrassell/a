"""
AWS Monitor Plugin

Plugin for monitoring AWS resources and services.
"""

from app.utils.plugin_base import PluginBase, PluginMetadata
from flask_login import login_required
from flask import render_template, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logger = logging.getLogger(__name__)

class AWSMonitorPlugin(PluginBase):
    """AWS Monitor plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name='AWS Monitor',
            version='1.0.0',
            description='Monitor AWS resources and services',
            author='Admin',
            required_roles=['admin', 'devops'],
            icon='fas fa-cloud',
            category='monitoring',
            weight=50
        )
        super().__init__(metadata)
        
        # Initialize blueprint with standard configuration
        self.init_blueprint(
            template_folder='templates',
            static_folder='static'
        )
        
        # Register routes
        self.register_routes()
        
        # Register models
        self.register_models()
        
        # Register CLI commands
        self.register_commands()
        
        # Register template filters
        self.register_template_filters()
        
        # Register context processors
        self.register_context_processors()

    def register_routes(self):
        """Register plugin routes."""
        if not self.blueprint:
            raise RuntimeError("Blueprint not initialized")

        # Import route modules
        from . import instance_routes, synthetic_routes, template_routes
        
        # Register routes from each module
        instance_routes.register_routes(self.blueprint)
        synthetic_routes.register_routes(self.blueprint)
        template_routes.register_routes(self.blueprint)

    def register_models(self):
        """Register plugin models."""
        try:
            from .models import init_models
            init_models()
            logger.info(f"Registered models for plugin: {self.metadata.name}")
        except ImportError:
            logger.info(f"No models to register for plugin: {self.metadata.name}")
        except Exception as e:
            logger.error(f"Error registering models: {e}")

    def register_commands(self):
        """Register plugin CLI commands."""
        if not self.blueprint:
            return

        @self.blueprint.cli.group()
        def awsmon():
            """AWS Monitor plugin commands."""
            pass

        @awsmon.command()
        def sync():
            """Sync AWS resources."""
            try:
                # Add sync logic here
                logger.info("Synced AWS resources")
            except Exception as e:
                logger.error(f"Error syncing AWS resources: {e}")
                raise

    def register_template_filters(self):
        """Register plugin template filters."""
        if not self.blueprint:
            return

        @self.blueprint.app_template_filter()
        def instance_status_class(status):
            """Convert instance status to CSS class."""
            status_classes = {
                'running': 'success',
                'stopped': 'warning',
                'terminated': 'danger'
            }
            return status_classes.get(status.lower(), 'secondary')

    def register_context_processors(self):
        """Register plugin context processors."""
        if not self.blueprint:
            return

        @self.blueprint.context_processor
        def inject_aws_regions():
            """Inject AWS regions into template context."""
            from .models import AWSRegion
            regions = AWSRegion.query.filter_by(enabled=True).all()
            return {
                'aws_regions': regions
            }

# Create plugin instance
plugin = AWSMonitorPlugin()
