"""Plugin functionality for projects blueprint."""

from flask import current_app
from flask_login import current_user

def can_access_projects(user):
    """Check if user can access projects functionality."""
    # Admin users always have access
    if any(role.name == 'Administrator' for role in user.roles):
        return True
        
    # Check for specific project permissions
    return any(role.name in ['Manager', 'User'] for role in user.roles)
