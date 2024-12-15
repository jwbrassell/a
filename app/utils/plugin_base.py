from flask import Blueprint, current_app, render_template
from typing import Optional, Dict, Any, List
import logging
from dataclasses import dataclass
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PluginMetadata:
    """Standard metadata for plugins."""
    name: str
    version: str
    description: str
    author: str
    required_roles: List[str]
    icon: str
    category: str
    weight: int = 0

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass

class PluginInitError(PluginError):
    """Exception raised when plugin initialization fails."""
    pass

class PluginConfigError(PluginError):
    """Exception raised when plugin configuration is invalid."""
    pass

def plugin_error_handler(f):
    """Decorator for standardized error handling in plugin routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in plugin route: {str(e)}")
            return render_template('error.html', 
                                error="Database error occurred", 
                                details=str(e)), 500
        except Exception as e:
            logger.error(f"Unexpected error in plugin route: {str(e)}")
            return render_template('error.html', 
                                error="An unexpected error occurred", 
                                details=str(e)), 500
    return decorated_function

class PluginBase:
    """Base class for all plugins."""
    
    def __init__(self, metadata: PluginMetadata):
        """Initialize plugin with metadata."""
        self.metadata = metadata
        self.blueprint = None
        self.logger = logging.getLogger(f"plugin.{metadata.name}")
        
        # Validate metadata
        self._validate_metadata()

    def _validate_metadata(self):
        """Validate plugin metadata."""
        required_fields = ['name', 'version', 'description', 'author', 
                         'required_roles', 'icon', 'category']
        for field in required_fields:
            if not getattr(self.metadata, field):
                raise PluginConfigError(f"Missing required metadata field: {field}")

    def init_blueprint(self, template_folder: Optional[str] = None, 
                      static_folder: Optional[str] = None) -> Blueprint:
        """Initialize Flask blueprint with standardized configuration."""
        if self.blueprint:
            return self.blueprint

        # Set up paths
        plugin_dir = Path(current_app.root_path) / 'plugins' / self.metadata.name
        
        if template_folder and not os.path.isdir(plugin_dir / template_folder):
            raise PluginInitError(f"Template directory not found: {template_folder}")
        
        if static_folder and not os.path.isdir(plugin_dir / static_folder):
            raise PluginInitError(f"Static directory not found: {static_folder}")

        # Create blueprint with standardized configuration
        self.blueprint = Blueprint(
            self.metadata.name,
            __name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path=f'/{self.metadata.name}/static',
            url_prefix=f'/{self.metadata.name}'
        )

        # Register standard error handlers
        self._register_error_handlers()
        
        return self.blueprint

    def _register_error_handlers(self):
        """Register standard error handlers for the plugin."""
        @self.blueprint.errorhandler(404)
        def handle_404(error):
            self.logger.warning(f"404 error in plugin {self.metadata.name}: {error}")
            return render_template('404.html'), 404

        @self.blueprint.errorhandler(500)
        def handle_500(error):
            self.logger.error(f"500 error in plugin {self.metadata.name}: {error}")
            return render_template('500.html'), 500

        @self.blueprint.errorhandler(SQLAlchemyError)
        def handle_db_error(error):
            self.logger.error(f"Database error in plugin {self.metadata.name}: {error}")
            return render_template('error.html', 
                                error="Database error occurred", 
                                details=str(error)), 500

    def init_app(self, app):
        """Initialize plugin with Flask application."""
        try:
            # Initialize plugin-specific logging
            if not app.debug:
                handler = logging.FileHandler(
                    filename=os.path.join(app.config['LOG_DIR'], 
                                        f'plugin_{self.metadata.name}.log')
                )
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s '
                    '[in %(pathname)s:%(lineno)d]'
                ))
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

            # Log initialization
            self.logger.info(f"Initialized plugin: {self.metadata.name} v{self.metadata.version}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {self.metadata.name}: {e}")
            raise PluginInitError(f"Failed to initialize plugin: {str(e)}")

    def register_routes(self):
        """Register routes for the plugin. Must be implemented by subclasses."""
        raise NotImplementedError("Plugins must implement register_routes()")

    def register_models(self):
        """Register models for the plugin. Must be implemented by subclasses."""
        raise NotImplementedError("Plugins must implement register_models()")

    def register_commands(self):
        """Register CLI commands for the plugin."""
        pass

    def register_template_filters(self):
        """Register template filters for the plugin."""
        pass

    def register_context_processors(self):
        """Register context processors for the plugin."""
        pass

    def register_before_request(self):
        """Register before_request handlers for the plugin."""
        pass

    def register_after_request(self):
        """Register after_request handlers for the plugin."""
        pass

    def register_teardown_request(self):
        """Register teardown_request handlers for the plugin."""
        pass

    def register_url_defaults(self):
        """Register URL defaults for the plugin."""
        pass

    def register_url_value_preprocessor(self):
        """Register URL value preprocessor for the plugin."""
        pass

    def register_static_resource(self, filename: str) -> str:
        """Register and return URL for static resource."""
        if not self.blueprint:
            raise PluginError("Blueprint not initialized")
        return f"{self.blueprint.static_url_path}/{filename}"

    def get_template_path(self, template_name: str) -> str:
        """Get full template path for the plugin."""
        return f"{self.metadata.name}/{template_name}"

    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log plugin action with standardized format."""
        log_entry = {
            'plugin': self.metadata.name,
            'version': self.metadata.version,
            'action': action,
            'details': details or {}
        }
        self.logger.info(f"Plugin action: {log_entry}")

    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled in configuration."""
        return current_app.config.get(f'PLUGIN_{self.metadata.name.upper()}_ENABLED', True)

    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin-specific configuration."""
        return current_app.config.get(f'PLUGIN_{self.metadata.name.upper()}_CONFIG', {})
