"""AWS Monitoring plugin for Flask application."""
from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="AWS Monitor",
    version="1.0.0",
    description="AWS infrastructure monitoring and management",
    author="System",
    required_roles=["admin", "user"],
    icon="fa-cloud",
    category="monitoring",
    weight=50
)

# Create blueprint with URL prefix
bp = Blueprint('awsmon', __name__, 
              template_folder='templates',
              static_folder='static',
              static_url_path='/awsmon/static',
              url_prefix='/awsmon')  # Add URL prefix

def init_app(app):
    """Initialize the AWS monitoring plugin"""
    from . import routes  # Import routes after Blueprint creation
    
    # Initialize plugin
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from . import models
    
    return bp

# Import routes after blueprint creation to avoid circular imports
from . import routes
