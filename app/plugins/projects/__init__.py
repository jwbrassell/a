"""Projects plugin for managing project tasks and tracking."""

from flask import Blueprint
from app.utils.plugin_manager import PluginMetadata

# Create blueprint
bp = Blueprint('projects', __name__,
               template_folder='templates',
               static_folder='static',
               url_prefix='/projects')

# Define plugin metadata
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

# Import routes and models after blueprint creation
from app.plugins.projects.routes import (
    main_routes,
    project_routes,
    status_routes,
    priority_routes,
    task_routes,
    todo_routes,
    comment_routes,
    subtask_routes
)
from app.plugins.projects import models
from .utils import init_project_settings

# Initialize project settings
init_project_settings()
