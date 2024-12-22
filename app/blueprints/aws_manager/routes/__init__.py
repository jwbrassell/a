"""
AWS Manager Routes Package
------------------------
This package contains all route handlers for the AWS Manager blueprint.
"""

from .configurations import *
from .health_events import *
from .ec2 import *
from .templates import *
from .security_groups import *
from .iam import *

__all__ = [
    # Core/Configuration Routes
    'index',
    'list_configurations',
    'create_configuration',
    'delete_configuration',
    
    # Health Events
    'list_health_events',
    'refresh_health_events',
    'get_health_event',
    
    # EC2 Instances
    'list_ec2_instances',
    'sync_ec2_instances',
    'list_tracked_instances',
    'launch_ec2_instance',
    'control_ec2_instance',
    
    # EC2 Templates
    'list_templates',
    'get_template',
    'create_template',
    'update_template',
    'delete_template',
    
    # Security Groups
    'list_security_groups',
    'get_security_group',
    'create_security_group',
    'delete_security_group',
    'add_security_group_rules',
    'remove_security_group_rules',
    
    # IAM Users
    'list_iam_users',
    'get_iam_user_details',
    'create_iam_user',
    'delete_iam_user',
    'rotate_iam_access_key',
    'attach_user_policy',
    'detach_user_policy',
    'list_available_policies',
    'add_user_to_group',
    'remove_user_from_group',
    'list_iam_groups',
]

# Route groups for documentation and organization purposes
ROUTE_GROUPS = {
    'configurations': [
        'index',
        'list_configurations',
        'create_configuration',
        'delete_configuration',
    ],
    'health_events': [
        'list_health_events',
        'refresh_health_events',
        'get_health_event',
    ],
    'ec2': [
        'list_ec2_instances',
        'sync_ec2_instances',
        'list_tracked_instances',
        'launch_ec2_instance',
        'control_ec2_instance',
    ],
    'templates': [
        'list_templates',
        'get_template',
        'create_template',
        'update_template',
        'delete_template',
    ],
    'security_groups': [
        'list_security_groups',
        'get_security_group',
        'create_security_group',
        'delete_security_group',
        'add_security_group_rules',
        'remove_security_group_rules',
    ],
    'iam': [
        'list_iam_users',
        'get_iam_user_details',
        'create_iam_user',
        'delete_iam_user',
        'rotate_iam_access_key',
        'attach_user_policy',
        'detach_user_policy',
        'list_available_policies',
        'add_user_to_group',
        'remove_user_from_group',
        'list_iam_groups',
    ]
}
