"""On-call rotation management plugin."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint with static folder
bp = Blueprint('oncall', __name__, 
              template_folder='templates',
              static_folder='static',
              static_url_path='/oncall/static',
              url_prefix='/oncall')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="On-Call Rotation",
    version="1.0.0",
    description="Manage and display on-call rotation schedules",
    author="System",
    required_roles=["admin"],  # For uploading schedules
    icon="fa-calendar-alt",
    category="Operations",
    weight=100
)

# Import models to ensure they're registered with SQLAlchemy
from . import models

# Import routes after models and blueprint creation
from . import routes
