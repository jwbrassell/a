from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('handoffs', __name__,
              template_folder='templates',
              url_prefix='/handoffs')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Handoffs",
    version="1.0.0",
    description="Manage shift handovers between teams with comprehensive tracking and metrics",
    author="System",
    required_roles=["user"],
    icon="fa-exchange-alt",
    category="Operations",
    weight=100
)

# Import routes after blueprint creation to avoid circular imports
from app.plugins.handoffs import routes
