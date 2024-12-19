"""Projects blueprint initialization."""

from flask import Blueprint

bp = Blueprint('projects', __name__, 
               template_folder='templates', 
               static_folder='static',
               url_prefix='/projects')

# Import routes after blueprint creation to avoid circular imports
from app.blueprints.projects import routes, models

def init_app(app):
    """Initialize the projects blueprint with the app."""
    app.register_blueprint(bp)
    return True
