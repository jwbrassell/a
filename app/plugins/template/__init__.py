"""
Template Plugin

This is a template for creating new plugins. Copy this directory and modify
it according to your needs.
"""

from app.utils.plugin_base import PluginBase, PluginMetadata
from flask_login import login_required
from flask import render_template, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TemplatePlugin(PluginBase):
    """Template plugin implementation."""
    
    def __init__(self):
        metadata = PluginMetadata(
            name='template',
            version='1.0.0',
            description='Template plugin for demonstration',
            author='Your Name',
            required_roles=['user'],
            icon='fas fa-puzzle-piece',
            category='utilities',
            weight=100
        )
        super().__init__(metadata)
        
        # Initialize blueprint with standard configuration
        self.init_blueprint(
            template_folder='templates',
            static_folder='static'
        )
        
        # Register routes
        self.register_routes()
        
        # Register models (if any)
        self.register_models()
        
        # Register CLI commands (if any)
        self.register_commands()
        
        # Register template filters (if any)
        self.register_template_filters()
        
        # Register context processors (if any)
        self.register_context_processors()

    def register_routes(self):
        """Register plugin routes."""
        if not self.blueprint:
            raise RuntimeError("Blueprint not initialized")

        @self.blueprint.route('/')
        @login_required
        def index():
            """Plugin index page."""
            try:
                self.log_action('view_index')
                return render_template(
                    self.get_template_path('index.html'),
                    plugin_name=self.metadata.name
                )
            except Exception as e:
                logger.error(f"Error in index route: {e}")
                return render_template('error.html', error=str(e)), 500

        @self.blueprint.route('/api/data')
        @login_required
        def get_data():
            """Example API endpoint."""
            try:
                self.log_action('get_data')
                data = {'message': 'Hello from template plugin!'}
                return jsonify(data)
            except Exception as e:
                logger.error(f"Error in get_data route: {e}")
                return jsonify({'error': str(e)}), 500

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
        def template():
            """Template plugin commands."""
            pass

        @template.command()
        def init():
            """Initialize plugin data."""
            try:
                # Add initialization logic here
                logger.info("Initialized template plugin data")
            except Exception as e:
                logger.error(f"Error initializing plugin data: {e}")
                raise

    def register_template_filters(self):
        """Register plugin template filters."""
        if not self.blueprint:
            return

        @self.blueprint.app_template_filter()
        def example_filter(value):
            """Example template filter."""
            return f"filtered_{value}"

    def register_context_processors(self):
        """Register plugin context processors."""
        if not self.blueprint:
            return

        @self.blueprint.context_processor
        def inject_plugin_info():
            """Inject plugin info into template context."""
            return {
                'plugin_version': self.metadata.version,
                'plugin_author': self.metadata.author
            }

# Create plugin instance
plugin = TemplatePlugin()
