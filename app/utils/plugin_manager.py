"""Plugin management system for Flask blueprints."""

import os
import importlib
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from flask import Flask, Blueprint
from app.models import Role
from app import db

logger = logging.getLogger(__name__)

@dataclass
class PluginMetadata:
    """Metadata for a blueprint plugin."""
    name: str
    version: str
    description: str
    author: str
    required_roles: List[str]
    icon: str
    category: str
    weight: int

class PluginManager:
    """Manages blueprint plugins for the Flask application."""
    
    def __init__(self, app: Flask, plugin_folder: str = 'plugins'):
        """Initialize the plugin manager."""
        self.app = app
        self.plugin_folder = os.path.join(app.root_path, plugin_folder)
        self.plugins: Dict[str, PluginMetadata] = {}
        
        # Create plugins directory if it doesn't exist
        os.makedirs(self.plugin_folder, exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugin directory."""
        plugins = []
        for item in os.listdir(self.plugin_folder):
            plugin_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(plugin_path) and \
               os.path.exists(os.path.join(plugin_path, '__init__.py')):
                plugins.append(item)
        return plugins
    
    def _create_roles(self, plugin_name: str, required_roles: List[str]):
        """Create roles if they don't exist."""
        try:
            for role_name in required_roles:
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    role = Role(
                        name=role_name,
                        notes=f"Created for plugin {plugin_name}",
                        icon="fa-puzzle-piece",
                        created_by="system"
                    )
                    db.session.add(role)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating roles for plugin {plugin_name}: {str(e)}")
            db.session.rollback()
    
    def load_plugin(self, plugin_name: str) -> Optional[Blueprint]:
        """Load a plugin by name."""
        try:
            # Import the plugin module
            module = importlib.import_module(f'app.plugins.{plugin_name}')
            
            # Get plugin metadata
            if not hasattr(module, 'plugin_metadata'):
                logger.error(f"Plugin {plugin_name} missing metadata")
                return None
            
            metadata = module.plugin_metadata
            if not isinstance(metadata, PluginMetadata):
                logger.error(f"Invalid metadata format for plugin {plugin_name}")
                return None
            
            # Store plugin metadata
            self.plugins[plugin_name] = metadata
            
            # Get the blueprint
            if not hasattr(module, 'bp'):
                logger.error(f"Plugin {plugin_name} missing blueprint")
                return None
            
            blueprint = module.bp
            if not isinstance(blueprint, Blueprint):
                logger.error(f"Invalid blueprint in plugin {plugin_name}")
                return None
            
            # Create any required roles
            self._create_roles(plugin_name, metadata.required_roles)
            
            # Initialize plugin if it has init_app function
            if hasattr(module, 'init_app'):
                module.init_app(self.app)
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            return None
    
    def load_all_plugins(self) -> List[Blueprint]:
        """Discover and load all available plugins."""
        blueprints = []
        for plugin_name in self.discover_plugins():
            blueprint = self.load_plugin(plugin_name)
            if blueprint:
                blueprints.append(blueprint)
        return blueprints
