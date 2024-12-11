from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

bp = Blueprint('weblinks', __name__, template_folder='templates', url_prefix='/weblinks')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Web Links",
    version="1.0.0",
    description="Manage and organize web links with categories, tags, and notes",
    author="System",
    required_roles=[],  # Empty list means accessible to all users
    icon="fa-link",
    category="Tools",
    weight=50
)

from app.plugins.weblinks import routes
