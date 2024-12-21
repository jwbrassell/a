"""Projects blueprint initialization."""

from flask import Blueprint

# Create blueprint with template and static folders
bp = Blueprint('projects', __name__, 
               template_folder='templates',
               static_folder='static',
               url_prefix='/projects')

# Import routes after blueprint creation to avoid circular imports
from . import routes

def init_app(app):
    """Initialize the projects blueprint with the app."""
    try:
        # Register the blueprint
        app.register_blueprint(bp)
        return True
    except Exception as e:
        app.logger.error(f"Error registering projects blueprint: {str(e)}")
        return False
