"""Dispatch plugin for managing and tracking dispatch requests."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('dispatch', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/dispatch')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Dispatch Tool",
    version="1.0.0",
    description="Manage and track dispatch requests with email notifications",
    author="System",
    required_roles=["user", "admin"],
    icon="fa-paper-plane",
    category="Tools",
    weight=100
)

# Import routes after blueprint creation
from app.plugins.dispatch import routes, models
from .utils.register_routes import register_dispatch_routes

def init_app(app):
    """Initialize the dispatch plugin"""
    with app.app_context():
        register_dispatch_routes()
