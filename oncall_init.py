"""On-call rotation management plugin."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('oncall', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/oncall')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="On-Call Rotation",
    version="1.0.0",
    description="Manage and display on-call rotation schedules",
    author="System",
    required_roles=["admin", "demo"],
    icon="fa-calendar-alt",
    category="Operations",
    weight=100
)

# Import routes after blueprint creation
from app.plugins.oncall import routes, models
