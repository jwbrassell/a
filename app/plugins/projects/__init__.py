"""Projects plugin for managing project tasks and tracking.

This plugin follows a structured organization pattern:

1. Core Setup:
   - Blueprint creation with proper template and static folders
   - Plugin metadata definition for system integration
   - Context processors for template utilities

2. Import Order:
   - Models and utils are imported first as they provide the foundational classes
   - Route utilities (can_edit_project, can_view_project) come next as they're used across routes
   - Main routes are imported last to ensure all dependencies are available

This structure ensures proper initialization and prevents circular imports while
maintaining a clear separation of concerns.
"""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint with proper static and template directories
bp = Blueprint('projects', __name__,
               template_folder='templates',
               static_folder='static',
               url_prefix='/projects')

# Define plugin metadata for system integration
plugin_metadata = PluginMetadata(
    name="Project Management",
    version="1.0.0",
    description="Manage and track projects, tasks, and progress",
    author="System",
    required_roles=["user", "admin"],
    icon="fa-project-diagram",
    category="Tools",
    weight=200
)

# Import models and utils first as they're required by routes
from app.plugins.projects import models
from .utils import init_project_settings
from .utils.register_routes import register_project_routes

# Import route utilities that are used across different route modules
from .routes.projects.utils import can_edit_project, can_view_project

# Import routes after all dependencies are available
# Routes are organized in routes/__init__.py to prevent conflicts
from app.plugins.projects.routes import main_routes
from app.plugins.projects.routes.tasks import crud as task_crud, dependencies, ordering
from app.plugins.projects.routes.projects import crud, team, todos

def init_app(app):
    """Initialize the projects plugin"""
    with app.app_context():
        init_project_settings()
        register_project_routes()

# Add template context processor for commonly used functions
@bp.app_context_processor
def utility_processor():
    """Make utility functions available in templates"""
    return {
        'can_edit_project': can_edit_project,
        'can_view_project': can_view_project
    }
