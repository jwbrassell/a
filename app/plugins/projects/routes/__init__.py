"""Routes for the projects plugin."""

from app.plugins.projects import bp

# Import all routes to register them with the main blueprint
from . import (
    main_routes,
    project_routes,
    status_routes,
    priority_routes,
    task_routes,
    comment_routes
)
