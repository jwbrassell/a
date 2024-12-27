from flask import Blueprint

# Create the blueprint
bp = Blueprint('database_reports', __name__, template_folder='templates', url_prefix='/database_reports')

# Import all routes from the modular files
from . import connections
from . import reports
from . import queries

# The routes are automatically registered with the blueprint
# through the imports above, so no additional code is needed here.
