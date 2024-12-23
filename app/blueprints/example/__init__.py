from flask import Blueprint

example = Blueprint('example', __name__, template_folder='templates', static_folder='static')

# Import routes after blueprint creation to avoid circular imports
from . import routes  # This registers the routes with the blueprint

# Make routes available at package level
from .routes import *
