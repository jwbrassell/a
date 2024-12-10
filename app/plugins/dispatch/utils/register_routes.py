"""Register dispatch routes in the PageRouteMapping table."""

from app.utils.route_manager import map_route_to_roles
from app.models import NavigationCategory
from app import db

def register_dispatch_routes():
    """Register all dispatch routes in the PageRouteMapping table."""
    
    # Get or create the Tools category
    tools_category = NavigationCategory.query.filter_by(name='Tools').first()
    if not tools_category:
        tools_category = NavigationCategory(
            name='Tools',
            icon='fa-tools',
            weight=200
        )
        db.session.add(tools_category)
        db.session.commit()

    # Map dispatch routes
    routes = [
        {
            'route': '/dispatch/',
            'page_name': 'Dispatch Tool',
            'icon': 'fa-paper-plane',
            'weight': 300,
            'roles': ['user']
        },
        {
            'route': '/dispatch/manage',
            'page_name': 'Manage Dispatch',
            'icon': 'fa-cog',
            'weight': 310,
            'roles': ['user']
        }
    ]

    # Register each route
    for route in routes:
        map_route_to_roles(
            route_path=route['route'],
            page_name=route['page_name'],
            roles=route['roles'],
            category_id=tools_category.id,
            icon=route['icon'],
            weight=route['weight']
        )
