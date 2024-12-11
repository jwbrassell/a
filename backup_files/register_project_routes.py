"""Script to register project routes in the database."""

from app import create_app, db
from app.models import NavigationCategory, PageRouteMapping, Role, User
from flask import current_app

def register_project_routes():
    """Register all project routes in the database."""
    print("Starting project route registration...")
    
    # Get or create the Tools category
    tools_category = NavigationCategory.query.filter_by(name='Tools').first()
    if not tools_category:
        tools_category = NavigationCategory(
            name='Tools',
            icon='fa-tools',
            weight=200,
            created_by='system'  # Only for NavigationCategory
        )
        db.session.add(tools_category)
        db.session.commit()
        print("Created Tools category")

    # Get the user role
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(
            name='user',
            notes='Default user role',
            icon='fa-user',
            created_by='system'  # Only for Role
        )
        db.session.add(user_role)
        db.session.commit()
        print("Created user role")

    # Define project routes
    routes = [
        {
            'route': 'projects.index',  # Using endpoint format
            'page_name': 'Projects',
            'icon': 'fa-project-diagram',
            'weight': 100,
            'show_in_navbar': True
        },
        {
            'route': 'projects.create_project',  # Using endpoint format
            'page_name': 'Create Project',
            'icon': 'fa-plus',
            'weight': 110,
            'show_in_navbar': True
        },
        {
            'route': 'projects.list_projects',  # Using endpoint format
            'page_name': 'Project List',
            'icon': 'fa-list',
            'weight': 120,
            'show_in_navbar': True
        }
    ]

    # Register each route
    for route_data in routes:
        # Check if route exists in Flask
        route_exists = False
        for rule in current_app.url_map.iter_rules():
            if rule.endpoint == route_data['route']:
                route_exists = True
                break
        
        if not route_exists:
            print(f"Warning: Route {route_data['route']} does not exist in Flask")
            continue

        # Get or create route mapping
        route_mapping = PageRouteMapping.query.filter_by(route=route_data['route']).first()
        if not route_mapping:
            route_mapping = PageRouteMapping(
                route=route_data['route'],
                page_name=route_data['page_name'],
                icon=route_data['icon'],
                weight=route_data['weight'],
                category_id=tools_category.id,
                show_in_navbar=route_data['show_in_navbar']
            )
            db.session.add(route_mapping)
            print(f"Created new route mapping for {route_data['route']}")
        else:
            # Update existing mapping
            route_mapping.page_name = route_data['page_name']
            route_mapping.icon = route_data['icon']
            route_mapping.weight = route_data['weight']
            route_mapping.category_id = tools_category.id
            route_mapping.show_in_navbar = route_data['show_in_navbar']
            print(f"Updated existing route mapping for {route_data['route']}")

        # Clear and set roles
        route_mapping.allowed_roles = []
        route_mapping.allowed_roles.append(user_role)

    # Commit changes
    try:
        db.session.commit()
        print("Successfully registered all project routes")
    except Exception as e:
        db.session.rollback()
        print(f"Error registering routes: {str(e)}")

def main():
    """Main function."""
    app = create_app()
    with app.app_context():
        # Print current routes in Flask
        print("\nCurrent Flask routes:")
        for rule in app.url_map.iter_rules():
            print(f"- {rule.rule} -> {rule.endpoint}")

        # Print current route mappings in database
        print("\nCurrent route mappings in database:")
        mappings = PageRouteMapping.query.all()
        for mapping in mappings:
            print(f"- {mapping.route} -> {mapping.page_name}")

        # Register routes
        print("\nRegistering project routes...")
        register_project_routes()

        # Print final route mappings
        print("\nFinal route mappings in database:")
        mappings = PageRouteMapping.query.all()
        for mapping in mappings:
            print(f"- {mapping.route} -> {mapping.page_name}")

if __name__ == '__main__':
    main()
