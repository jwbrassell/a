from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Admin Dashboard",
    version="1.0.0",
    description="Administrative interface for managing roles, routes, navigation, and system monitoring",
    author="System",
    required_roles=["admin"],
    icon="fa-cogs",
    category="System",
    weight=0  # Show first in navigation
)

# Import routes after blueprint creation to avoid circular imports
from app.plugins.admin import routes
from app.plugins.admin import monitoring

# Register the monitoring blueprint
bp.register_blueprint(monitoring.bp)
