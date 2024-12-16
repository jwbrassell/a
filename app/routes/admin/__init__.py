"""Admin module initialization."""
from flask import Blueprint

# Create Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes after Blueprint creation to avoid circular imports
from . import routes  # noqa: F401, E402
from . import roles  # noqa: F401, E402
from . import icons  # noqa: F401, E402
from . import api_users  # noqa: F401, E402

# Register error handlers
from app.utils.enhanced_rbac import PermissionDenied

@admin_bp.errorhandler(PermissionDenied)
def handle_permission_denied(error):
    """Handle permission denied errors."""
    return error.get_response()

@admin_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@admin_bp.errorhandler(500)
def handle_server_error(error):
    """Handle 500 errors."""
    return render_template('500.html'), 500

# Import required modules
from flask import render_template  # noqa: E402
