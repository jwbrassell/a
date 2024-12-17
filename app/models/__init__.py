"""Models package initialization."""
from app.models.permission import Permission
from app.models.permissions import Action, RoutePermission
from app.models.role import Role
from app.models.user import User, UserPreference
from app.models.navigation import NavigationCategory, PageRouteMapping, route_roles
from app.models.activity import UserActivity, PageVisit
from app.models.documents import (
    Document,
    DocumentCategory,
    DocumentTag,
    DocumentChange,
    DocumentShare,
    DocumentCache,
    document_tag_association
)
from app.models.dispatch import DispatchSettings, DispatchHistory

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
    'route_roles',
    # Document models
    'Document',
    'DocumentCategory',
    'DocumentTag',
    'DocumentChange',
    'DocumentShare',
    'DocumentCache',
    'document_tag_association',
    # Dispatch models
    'DispatchSettings',
    'DispatchHistory'
]
