"""Routes for the projects plugin."""

from app.plugins.projects import bp

# Import project-specific routes first
from .projects import crud, team, todos

# Import task-specific routes
from .tasks import crud as task_crud, dependencies, ordering

# Import other routes after specific routes
from . import (
    main_routes,
    project_routes,
    task_routes,
    comment_routes,
    subtask_routes,
    management_routes
)
