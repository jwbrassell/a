from flask import current_app
from app.models import NavigationCategory, PageRouteMapping
from app.extensions import db
from app.utils.enhanced_rbac import register_permission

def init_plugin(app):
    """Initialize AWS manager plugin"""
    # Register required permissions
    permissions = [
        {
            'name': 'aws_access',
            'description': 'Access AWS manager'
        },
        {
            'name': 'aws_create_config',
            'description': 'Create AWS configurations'
        },
        {
            'name': 'aws_delete_config',
            'description': 'Delete AWS configurations'
        },
        {
            'name': 'aws_manage_ec2',
            'description': 'Manage EC2 instances'
        },
        {
            'name': 'aws_manage_iam',
            'description': 'Manage IAM users'
        },
        {
            'name': 'aws_manage_security',
            'description': 'Manage security groups'
        },
        {
            'name': 'aws_manage_templates',
            'description': 'Manage EC2 templates'
        }
    ]
    
    # Create permissions if they don't exist
    for permission in permissions:
        register_permission(
            permission['name'],
            permission['description'],
            actions=['read', 'write', 'update', 'delete']
        )
    
    # Register navigation
    with app.app_context():
        register_navigation()

def register_navigation():
    """Register AWS manager navigation items"""
    try:
        # Create or get Infrastructure category
        category = NavigationCategory.query.filter_by(name='Infrastructure').first()
        if not category:
            category = NavigationCategory(
                name='Infrastructure',
                icon='fa-server',
                weight=100,
                created_by='system'
            )
            db.session.add(category)
            db.session.flush()  # Get the ID without committing

        # Create route mapping for AWS Manager
        main_route = PageRouteMapping.query.filter_by(route='/aws/configurations').first()
        if not main_route:
            main_route = PageRouteMapping(
                page_name='AWS Manager',
                route='/aws/configurations',
                icon='fa-cloud',
                category=category,  # Use the relationship directly
                show_in_navbar=True,
                weight=10,
                description='Manage AWS resources and configurations',
                created_by='system',
                nav_category='aws',  # For breadcrumb support
                breadcrumb_text='AWS Manager'
            )
            db.session.add(main_route)
            db.session.flush()  # Get the ID for parent reference

        # Create route mappings for sub-pages
        sub_routes = [
            {
                'route': '/aws/configurations/<int:config_id>/ec2',
                'page_name': 'EC2 Instances',
                'icon': 'fa-server',
                'weight': 20,
                'description': 'Manage EC2 instances across regions',
                'nav_category': 'aws.ec2',
                'breadcrumb_text': 'EC2 Instances'
            },
            {
                'route': '/aws/configurations/<int:config_id>/iam',
                'page_name': 'IAM Users',
                'icon': 'fa-users',
                'weight': 30,
                'description': 'Manage IAM users and access keys',
                'nav_category': 'aws.iam',
                'breadcrumb_text': 'IAM Users'
            },
            {
                'route': '/aws/configurations/<int:config_id>/security-groups',
                'page_name': 'Security Groups',
                'icon': 'fa-shield-alt',
                'weight': 40,
                'description': 'Manage EC2 security groups and rules',
                'nav_category': 'aws.security',
                'breadcrumb_text': 'Security Groups'
            },
            {
                'route': '/aws/configurations/<int:config_id>/templates',
                'page_name': 'EC2 Templates',
                'icon': 'fa-copy',
                'weight': 50,
                'description': 'Manage EC2 launch templates',
                'nav_category': 'aws.templates',
                'breadcrumb_text': 'EC2 Templates'
            }
        ]

        for sub_route in sub_routes:
            existing = PageRouteMapping.query.filter_by(route=sub_route['route']).first()
            if not existing:
                new_route = PageRouteMapping(
                    page_name=sub_route['page_name'],
                    route=sub_route['route'],
                    icon=sub_route['icon'],
                    category=category,
                    show_in_navbar=False,  # Sub-routes don't show in navbar
                    weight=sub_route['weight'],
                    description=sub_route['description'],
                    created_by='system',
                    nav_category=sub_route['nav_category'],
                    breadcrumb_text=sub_route['breadcrumb_text'],
                    parent=main_route  # Set parent for proper navigation hierarchy
                )
                db.session.add(new_route)

        # Add dynamic route for configuration details
        config_route = PageRouteMapping.query.filter_by(route='/aws/configurations/<int:config_id>').first()
        if not config_route:
            config_route = PageRouteMapping(
                page_name='Configuration Details',
                route='/aws/configurations/<int:config_id>',
                icon='fa-cog',
                category=category,
                show_in_navbar=False,
                weight=15,
                description='AWS Configuration Details',
                created_by='system',
                nav_category='aws.config',
                breadcrumb_text='Configuration',
                parent=main_route
            )
            db.session.add(config_route)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to register AWS manager navigation: {str(e)}")
        return False

def get_breadcrumb_data(route, **kwargs):
    """Get breadcrumb data for AWS manager routes"""
    try:
        # Get the route mapping
        route_mapping = PageRouteMapping.query.filter_by(route=route).first()
        if not route_mapping:
            return None

        # Build breadcrumb trail
        breadcrumbs = []
        current = route_mapping
        while current:
            # Format the route with kwargs if needed
            formatted_route = current.route
            if kwargs and '<int:config_id>' in formatted_route:
                formatted_route = formatted_route.replace('<int:config_id>', str(kwargs.get('config_id', '')))

            breadcrumbs.insert(0, {
                'text': current.breadcrumb_text,
                'url': formatted_route if current != route_mapping else None  # Last item is not a link
            })
            current = current.parent

        return breadcrumbs
    except Exception as e:
        current_app.logger.error(f"Failed to get breadcrumb data: {str(e)}")
        return None
