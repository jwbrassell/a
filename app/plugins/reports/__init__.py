"""Reports plugin for self-service report generation."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata
import os

# Create blueprint with static folder
bp = Blueprint('reports', __name__, 
              template_folder='templates',
              static_folder='static',
              static_url_path='/reports/static',
              url_prefix='/reports')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Reports",
    version="1.0.0",
    description="Self-service report generation system",
    author="System",
    required_roles=["admin"],
    icon="fa-chart-bar",
    category="Admin",
    weight=100
)

# Import models to ensure they're registered with SQLAlchemy
from . import models

# Import and register template filters
from . import template_filters
template_filters.register_template_filters(bp)

# Import routes after models and blueprint creation
from . import routes
