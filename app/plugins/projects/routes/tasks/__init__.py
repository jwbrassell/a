"""Task management routes initialization."""

from . import crud, dependencies, ordering, utils

# Export utility functions for use in other modules
from .utils import (
    serialize_date,
    get_available_tasks,
    create_task_history,
    log_task_activity,
    track_task_changes,
    validate_task_data
)

# Export all modules and functions
__all__ = [
    'crud',
    'dependencies',
    'ordering',
    'utils',
    # Utility functions
    'serialize_date',
    'get_available_tasks',
    'create_task_history',
    'log_task_activity',
    'track_task_changes',
    'validate_task_data'
]
