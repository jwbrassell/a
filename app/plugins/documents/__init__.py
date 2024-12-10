from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

bp = Blueprint('documents', __name__, template_folder='templates', url_prefix='/documents')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Documents",
    version="1.0.0",
    description="Document management and knowledge base",
    author="System",
    required_roles=["admin", "user"],
    icon="fa-file-alt",
    category="Documentation",
    weight=50
)

from app.plugins.documents import routes
