"""Models package initialization."""
from app.extensions import login_manager
from app.models.permissions import Permission, Action, RoutePermission
from app.models.role import Role
from app.models.user import User, UserPreference
from app.models.navigation import NavigationCategory, PageRouteMapping, route_roles
from app.models.activity import UserActivity, PageVisit

__all__ = [
    'Permission',
    'Action',
    'RoutePermission',
    'Role',
    'User',
    'UserPreference',
    'NavigationCategory',
    'PageRouteMapping',
    'UserActivity',
    'PageVisit',
    'route_roles'
]

@login_manager.user_loader
def load_user(id):
    """Load user by ID."""
    return User.query.get(int(id))
