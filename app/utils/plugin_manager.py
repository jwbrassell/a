import os
import sys
import importlib
import logging
from typing import Dict, List, Optional, Type
from flask import Flask, Blueprint
from pathlib import Path
from app.utils.plugin_base import PluginBase, PluginError, PluginMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin loading, initialization, and lifecycle."""
    
    def __init__(self, app: Optional[Flask] = None):
        """Initialize plugin manager."""
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_dir = None
        self.app = None
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize plugin manager with Flask application."""
        self.app = app
        self.plugin_dir = Path(app.root_path) / 'plugins'
        
        # Create plugin directory if it doesn't exist
        os.makedirs(self.plugin_dir, exist_ok=True)
        
        # Configure plugin-specific settings
        app.config.setdefault('PLUGIN_ENABLED', True)
        app.config.setdefault('PLUGIN_AUTO_LOAD', True)
        app.config.setdefault('PLUGIN_BLACKLIST', [])
        
        # Add plugin directory to Python path
        if str(self.plugin_dir) not in sys.path:
            sys.path.insert(0, str(self.plugin_dir))
        
        # Auto-load plugins if configured
        if app.config['PLUGIN_AUTO_LOAD']:
            self.load_all_plugins()

    def _is_plugin_directory(self, path: Path) -> bool:
        """Check if a directory is a valid plugin directory."""
        return (
            path.is_dir() and
            not path.name.startswith('_') and
            not path.name.startswith('.') and
            (path / '__init__.py').exists()
        )

    def _import_plugin_module(self, plugin_name: str):
        """Import plugin module safely."""
        try:
            return importlib.import_module(f"app.plugins.{plugin_name}")
        except ImportError as e:
            logger.error(f"Failed to import plugin {plugin_name}: {e}")
            return None

    def _validate_plugin_class(self, plugin_module) -> Optional[Type[PluginBase]]:
        """Validate and return plugin class from module."""
        # Look for a class that inherits from PluginBase
        plugin_classes = [
            obj for name, obj in plugin_module.__dict__.items()
            if isinstance(obj, type) and 
            issubclass(obj, PluginBase) and 
            obj != PluginBase
        ]
        
        if not plugin_classes:
            logger.error(f"No valid plugin class found in {plugin_module.__name__}")
            return None
        
        if len(plugin_classes) > 1:
            logger.warning(f"Multiple plugin classes found in {plugin_module.__name__}, using first")
        
        return plugin_classes[0]

    def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Load and initialize a single plugin."""
        try:
            # Skip if plugin is blacklisted
            if plugin_name in self.app.config['PLUGIN_BLACKLIST']:
                logger.info(f"Skipping blacklisted plugin: {plugin_name}")
                return None
            
            # Skip if already loaded
            if plugin_name in self.plugins:
                logger.info(f"Plugin already loaded: {plugin_name}")
                return self.plugins[plugin_name]
            
            # Import plugin module
            plugin_module = self._import_plugin_module(plugin_name)
            if not plugin_module:
                return None
            
            # Get plugin class
            plugin_class = self._validate_plugin_class(plugin_module)
            if not plugin_class:
                return None
            
            # Initialize plugin
            plugin = plugin_class()
            
            # Initialize blueprint
            if hasattr(plugin, 'init_blueprint'):
                plugin.init_blueprint()
            
            # Initialize with app
            plugin.init_app(self.app)
            
            # Register plugin
            self.plugins[plugin_name] = plugin
            
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return None

    def load_all_plugins(self) -> List[Blueprint]:
        """Load all plugins from the plugins directory."""
        loaded_blueprints = []
        
        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return loaded_blueprints
        
        # Get all plugin directories
        plugin_dirs = [
            d for d in self.plugin_dir.iterdir()
            if self._is_plugin_directory(d)
        ]
        
        # Sort by plugin weight and name
        plugin_dirs.sort(key=lambda d: (
            self._get_plugin_weight(d),
            d.name
        ))
        
        # Load each plugin
        for plugin_dir in plugin_dirs:
            plugin = self.load_plugin(plugin_dir.name)
            if plugin and plugin.blueprint and plugin.blueprint.name not in self.app.blueprints:
                loaded_blueprints.append(plugin.blueprint)
        
        return loaded_blueprints

    def _get_plugin_weight(self, plugin_dir: Path) -> int:
        """Get plugin weight for sorting."""
        try:
            module = self._import_plugin_module(plugin_dir.name)
            if module and hasattr(module, 'plugin_metadata'):
                return getattr(module.plugin_metadata, 'weight', 0)
        except Exception:
            pass
        return 0

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name."""
        return self.plugins.get(plugin_name)

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        try:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin not loaded: {plugin_name}")
                return False
            
            plugin = self.plugins[plugin_name]
            
            # Remove blueprint registration
            if plugin.blueprint and plugin.blueprint.name in self.app.blueprints:
                self.app.blueprints.pop(plugin.blueprint.name)
                
                # Clean up URL map
                for rule in list(self.app.url_map.iter_rules()):
                    if rule.endpoint.startswith(f"{plugin.blueprint.name}."):
                        self.app.url_map._rules.remove(rule)
            
            # Remove plugin instance
            del self.plugins[plugin_name]
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def reload_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Reload a plugin."""
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)

    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata."""
        plugin = self.get_plugin(plugin_name)
        return plugin.metadata if plugin else None

    def get_enabled_plugins(self) -> List[str]:
        """Get list of enabled plugin names."""
        return [
            name for name, plugin in self.plugins.items()
            if plugin.is_enabled
        ]

    def get_plugin_config(self, plugin_name: str) -> dict:
        """Get plugin configuration."""
        plugin = self.get_plugin(plugin_name)
        return plugin.config if plugin else {}

    def validate_plugin_dependencies(self, plugin_name: str) -> bool:
        """Validate plugin dependencies."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return False
        
        # Check required plugins
        required_plugins = getattr(plugin.metadata, 'required_plugins', [])
        for required in required_plugins:
            if required not in self.plugins:
                logger.error(f"Missing required plugin: {required}")
                return False
        
        return True

    def get_plugin_routes(self, plugin_name: str) -> List[str]:
        """Get list of routes registered by a plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin or not plugin.blueprint:
            return []
        
        return [
            str(rule) for rule in self.app.url_map.iter_rules()
            if rule.endpoint.startswith(f"{plugin.blueprint.name}.")
        ]

    def get_plugin_templates(self, plugin_name: str) -> List[str]:
        """Get list of templates available to a plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin or not plugin.blueprint:
            return []
        
        template_folder = Path(plugin.blueprint.template_folder)
        if not template_folder.exists():
            return []
        
        templates = []
        for path in template_folder.rglob('*.html'):
            templates.append(str(path.relative_to(template_folder)))
        
        return templates
