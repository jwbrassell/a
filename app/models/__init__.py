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
from app.models.handoffs import WorkCenter, WorkCenterMember, HandoffSettings, Handoff
from app.models.metrics import Metric, MetricAlert, MetricDashboard
from app.models.analytics import (
    FeatureUsage,
    DocumentAnalytics,
    ProjectMetrics,
    TeamProductivity,
    ResourceUtilization
)
# Import AWS models lazily to avoid circular imports
def get_aws_models():
    from app.blueprints.aws_manager.models.ec2_instance import EC2Instance
    from app.blueprints.aws_manager.models.ec2_template import EC2Template
    from app.blueprints.aws_manager.models.aws_configuration import AWSConfiguration
    from app.blueprints.aws_manager.models.health_event import AWSHealthEvent
    return EC2Instance, EC2Template, AWSConfiguration, AWSHealthEvent

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
    'DispatchHistory',
    # Handoff models
    'WorkCenter',
    'WorkCenterMember',
    'HandoffSettings',
    'Handoff',
    # Metrics models
    'Metric',
    'MetricAlert',
    'MetricDashboard',
    # Analytics models
    'FeatureUsage',
    'DocumentAnalytics',
    'ProjectMetrics',
    'TeamProductivity',
    'ResourceUtilization',
    # AWS models are loaded lazily via get_aws_models()
]
