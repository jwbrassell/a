"""User profile management plugin."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.plugin_manager import PluginMetadata

# Create the blueprint
bp = Blueprint('profile', __name__,
              template_folder='templates',
              static_folder='static',  # Add static folder like hello plugin
              url_prefix='/profile')

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="User Profile",  # Full name
    version="1.0.0",
    description="User profile management plugin",
    author="System",
    required_roles=[],  # No specific roles required, just authentication
    icon="fa-user",
    category="User",  # Navigation category
    weight=98  # Position above logout
)

# Define routes
@bp.route('/')
@login_required
def index():
    """User profile page."""
    return render_template('profile/index.html', user=current_user)
