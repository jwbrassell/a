from app import db, create_app
from app.models import NavigationCategory, PageRouteMapping, Role

def add_admin_route():
    """Add admin dashboard route to navigation under Admin category."""
    app = create_app()
    with app.app_context():
        # Get the Admin category
        admin_category = NavigationCategory.query.filter_by(name='Admin').first()
        if not admin_category:
            admin_category = NavigationCategory(
                name='Admin',
                description='Administrative functions',
                icon='fa-shield-alt',
                weight=100,  # High weight to appear at the bottom
                created_by='system'
            )
            db.session.add(admin_category)
            db.session.flush()  # Flush to get the category ID

        # Get admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("Error: Admin role not found")
            return

        # Add admin dashboard route if it doesn't exist
        admin_route = PageRouteMapping.query.filter_by(route='admin/index').first()
        if not admin_route:
            admin_route = PageRouteMapping(
                page_name='Admin Dashboard',
                route='admin/index',  # Store in a format that can be converted to both URL and endpoint
                icon='fa-tachometer-alt',
                weight=0,  # First item in Admin category
                category_id=admin_category.id
            )
            admin_route.allowed_roles.append(admin_role)
            db.session.add(admin_route)

        try:
            db.session.commit()
            print("Successfully added admin dashboard route")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding admin route: {str(e)}")

if __name__ == '__main__':
    add_admin_route()
