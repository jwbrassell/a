"""Plugin management system for Flask blueprints."""

import os
import importlib
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from flask import Flask, Blueprint
from app.models import Role, PageRouteMapping
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
        """Initialize the plugin manager.
        
        Args:
            app: Flask application instance
            plugin_folder: Folder containing plugins (relative to app directory)
        """
        self.app = app
        self.plugin_folder = os.path.join(app.root_path, plugin_folder)
        self.plugins: Dict[str, PluginMetadata] = {}
        
        # Create plugins directory if it doesn't exist
        os.makedirs(self.plugin_folder, exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugin directory.
        
        Returns:
            List of plugin names found in the plugin directory.
        """
        plugins = []
        
        # Look for plugin packages (directories with __init__.py)
        for item in os.listdir(self.plugin_folder):
            plugin_path = os.path.join(self.plugin_folder, item)
            if os.path.isdir(plugin_path) and \
               os.path.exists(os.path.join(plugin_path, '__init__.py')):
                plugins.append(item)
        
        return plugins
    
    def load_plugin(self, plugin_name: str) -> Optional[Blueprint]:
        """Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            Loaded blueprint or None if loading fails
        """
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
            
            # Register plugin routes in database
            self._register_plugin_routes(plugin_name, metadata)
            
            return blueprint
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            return None
    
    def _register_plugin_routes(self, plugin_name: str, metadata: PluginMetadata):
        """Register plugin routes in the database.
        
        Args:
            plugin_name: Name of the plugin
            metadata: Plugin metadata
        """
        try:
            # Create roles if they don't exist
            for role_name in metadata.required_roles:
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    role = Role(
                        name=role_name,
                        notes=f"Created for plugin {plugin_name}",
                        icon="fa-puzzle-piece",
                        created_by="system"
                    )
                    db.session.add(role)
            
            # Create route mapping
            route_name = f"{plugin_name}.index"
            existing_route = PageRouteMapping.query.filter_by(route=route_name).first()
            
            if not existing_route:
                route = PageRouteMapping(
                    page_name=metadata.name,
                    route=route_name,
                    icon=metadata.icon,
                    weight=metadata.weight
                )
                
                # Assign roles
                roles = Role.query.filter(Role.name.in_(metadata.required_roles)).all()
                route.allowed_roles.extend(roles)
                
                db.session.add(route)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error registering routes for plugin {plugin_name}: {str(e)}")
            db.session.rollback()
    
    def load_all_plugins(self) -> List[Blueprint]:
        """Discover and load all available plugins.
        
        Returns:
            List of loaded blueprints
        """
        blueprints = []
        
        for plugin_name in self.discover_plugins():
            blueprint = self.load_plugin(plugin_name)
            if blueprint:
                blueprints.append(blueprint)
        
        return blueprints
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get metadata for a loaded plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin metadata or None if plugin not loaded
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugin_metadata(self) -> Dict[str, PluginMetadata]:
        """Get metadata for all loaded plugins.
        
        Returns:
            Dictionary of plugin names to metadata
        """
        return self.plugins.copy()
