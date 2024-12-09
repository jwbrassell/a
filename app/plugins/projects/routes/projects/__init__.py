"""Project management routes initialization."""

from app.plugins.projects import bp
from . import crud, team, todos, utils

# Import all routes to register them with the blueprint
from .crud import (
    list_projects,
    create_project,
    create_project_post,
    edit_project,
    update_project,
    delete_project
)

from .team import (
    get_project_team,
    update_project_watchers,
    update_project_stakeholders,
    update_project_shareholders,
    update_project_roles
)

from .todos import (
    get_project_todos,
    create_project_todo,
    reorder_project_todos,
    update_project_todo,
    delete_project_todo
)

# Export utility functions for use in other modules
from .utils import (
    serialize_date,
    create_project_history,
    log_project_activity,
    track_project_changes,
    validate_project_data,
    can_edit_project,
    can_view_project,
    get_project_stats
)

# List of all route functions for documentation and testing
routes = [
    # CRUD operations
    list_projects,
    create_project,
    create_project_post,
    edit_project,
    update_project,
    delete_project,
    
    # Team management
    get_project_team,
    update_project_watchers,
    update_project_stakeholders,
    update_project_shareholders,
    update_project_roles,
    
    # Todo management
    get_project_todos,
    create_project_todo,
    reorder_project_todos,
    update_project_todo,
    delete_project_todo
]

# Export all modules and functions
__all__ = [
    'crud',
    'team',
    'todos',
    'utils',
    'routes',
    # Utility functions
    'serialize_date',
    'create_project_history',
    'log_project_activity',
    'track_project_changes',
    'validate_project_data',
    'can_edit_project',
    'can_view_project',
    'get_project_stats'
]
