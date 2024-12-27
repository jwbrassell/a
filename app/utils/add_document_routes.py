from app.extensions import db
from app.models import NavigationCategory, PageRouteMapping, Role

def add_document_routes():
    """Add document routes to navigation under Documentation category."""
    try:
        # Get or create Documentation category
        docs_category = NavigationCategory.query.filter_by(name='Documentation').first()
        if not docs_category:
            docs_category = NavigationCategory(
                name='Documentation',
                description='Document management and knowledge base',
                icon='fa-book',
                weight=50,  # Middle weight
                created_by='system'
            )
            db.session.add(docs_category)
            db.session.flush()

        # Get roles that should have access
        admin_role = Role.query.filter_by(name='Administrator').first()
        user_role = Role.query.filter_by(name='user').first()
        if not admin_role or not user_role:
            print("Error: Required roles not found")
            return

        # Define routes to add
        routes = [
            {
                'page_name': 'Documents',
                'route': 'documents/index',
                'icon': 'fa-file-alt',
                'weight': 0,
                'roles': [admin_role, user_role]
            },
            {
                'page_name': 'Search Documents',
                'route': 'documents/search',
                'icon': 'fa-search',
                'weight': 1,
                'roles': [admin_role, user_role]
            },
            {
                'page_name': 'Categories',
                'route': 'documents/categories',
                'icon': 'fa-folder',
                'weight': 2,
                'roles': [admin_role]
            },
            {
                'page_name': 'Tags',
                'route': 'documents/tags',
                'icon': 'fa-tags',
                'weight': 3,
                'roles': [admin_role]
            }
        ]

        # Add routes
        for route_data in routes:
            route = PageRouteMapping.query.filter_by(route=route_data['route']).first()
            if not route:
                route = PageRouteMapping(
                    page_name=route_data['page_name'],
                    route=route_data['route'],
                    icon=route_data['icon'],
                    weight=route_data['weight'],
                    category_id=docs_category.id,
                    show_in_navbar=True
                )
                route.allowed_roles.extend(route_data['roles'])
                db.session.add(route)

        try:
            db.session.commit()
            print("Successfully added document routes")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding document routes: {str(e)}")
