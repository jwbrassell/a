"""Routes for the projects plugin.

This module organizes route imports in a specific order to avoid conflicts and maintain
a clear hierarchy of functionality:

1. Project-specific routes (crud, team, todos) are imported first as they contain
   the core CRUD operations and base functionality that other routes may depend on.
   The crud.py module specifically contains the primary view_project route that
   serves as the main entry point for viewing projects.

2. Task-specific routes (crud, dependencies, ordering) come next as they build upon
   the project functionality but handle task-level operations. These are kept
   separate to maintain clear boundaries between project and task operations.

3. Main routes are imported after the core functionality is established, as they
   often provide overview pages and dashboards that may need to reference both
   projects and tasks.

4. Supporting feature routes (tasks, comments, subtasks) are imported last as they
   represent auxiliary functionality that enhances the core features.

This organization helps prevent route conflicts (like duplicate view_project routes)
and maintains a clear separation of concerns between different aspects of the plugin.
"""

from app.plugins.projects import bp

# Core project functionality
# These routes handle the fundamental CRUD operations for projects
from .projects import crud, team, todos

# Task management functionality
# These routes handle task-specific operations that build upon projects
from .tasks import crud as task_crud, dependencies, ordering

# Main routes for overview pages
# These provide high-level views that may combine project and task data
from . import main_routes

# Task-related routes
# These handle specific task views and operations
from . import task_routes

# Comment functionality
# These routes handle the comment system for projects and tasks
from . import comment_routes

# Subtask management
# These routes handle operations specific to subtasks
from . import subtask_routes

# Administrative and management features
# These routes handle system-wide operations and settings
from . import management_routes

# Note: project_routes is intentionally not imported as its functionality
# is now properly organized in the crud.py module to avoid route conflicts
