from flask import Blueprint

bp = Blueprint('database_reports', __name__, template_folder='templates', url_prefix='/database_reports')

# Import models first to avoid circular imports
from .models import DatabaseConnection, Report, ReportTagModel as Tag, ReportHistory

# Import utility functions
from .utils import format_value, execute_query, validate_sql_query

# Import all route modules
from . import connections
from . import reports
from . import queries
from . import routes

# Import plugin initialization
from .plugin import init_app

# This ensures all routes are registered with the blueprint
# The order of imports is important to avoid circular dependencies
