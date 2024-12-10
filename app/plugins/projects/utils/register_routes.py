"""Register project routes in the PageRouteMapping table."""

from app.utils.route_manager import map_route_to_roles
from app.models import NavigationCategory
from app import db

def register_project_routes():
    """Register all project routes in the PageRouteMapping table."""
    
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

    # Map main project routes
    routes = [
        {
            'route': '/projects/',  # Main projects page
            'page_name': 'Projects',
            'icon': 'fa-project-diagram',
            'weight': 100,
            'roles': ['user']
        },
        {
            'route': '/projects/create',  # Create project page
            'page_name': 'Create Project',
            'icon': 'fa-plus',
            'weight': 110,
            'roles': ['user']
        },
        {
            'route': '/projects/list',  # Project listing
            'page_name': 'Project List',
            'icon': 'fa-list',
            'weight': 120,
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
