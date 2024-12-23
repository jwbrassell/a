"""On-call rotation management blueprint."""

from flask import Blueprint

bp = Blueprint('oncall', __name__, 
              template_folder='templates',
              static_folder='static',
              url_prefix='/oncall')

# Import routes after blueprint creation to avoid circular imports
from app.blueprints.oncall import routes, models

def init_app(app):
    """Initialize the oncall blueprint with the app."""
    app.register_blueprint(bp)
