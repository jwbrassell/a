"""Weblinks management blueprint."""

from flask import Blueprint

bp = Blueprint('weblinks', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/weblinks')

# Import routes after blueprint creation to avoid circular imports
from app.blueprints.weblinks import routes, models
from .init_roles import init_weblinks_roles

def init_app(app):
    """Initialize the weblinks blueprint with the app."""
    init_weblinks_roles()  # Initialize roles and permissions
    app.register_blueprint(bp)
    return True
