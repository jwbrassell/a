"""Projects plugin for comprehensive project management."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('projects', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/projects')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Projects",
    version="1.0.0",
    description="Comprehensive project management system with tasks, todos, and collaboration features",
    author="System",
    required_roles=["user"],
    icon="fa-project-diagram",
    category="Management",
    weight=50
)

# Import routes after blueprint creation
from app.plugins.projects import routes, models
