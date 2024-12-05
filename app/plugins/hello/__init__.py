"""Example plugin demonstrating the plugin system."""

from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.plugin_manager import PluginMetadata
from app.utils.rbac import requires_roles

# Create the blueprint
bp = Blueprint('hello', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/hello')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Hello Plugin",
    version="1.0.0",
    description="An example plugin demonstrating the plugin system",
    author="System",
    required_roles=["user"],  # Basic user role required
    icon="fa-hand-wave",  # FontAwesome icon
    category="Examples",  # Navigation category
    weight=100  # Order in navigation
)

# Define routes
@bp.route('/')
@login_required
@requires_roles('user')
def index():
    """Main plugin page."""
    return render_template('hello/index.html', 
                         title="Hello Plugin",
                         description=plugin_metadata.description)

@bp.route('/about')
@login_required
@requires_roles('user')
def about():
    """About page showing plugin information."""
    return render_template('hello/about.html',
                         metadata=plugin_metadata)
