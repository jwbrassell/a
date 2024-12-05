from app import db, create_app
from app.models import NavigationCategory, PageRouteMapping, Role
from sqlalchemy import text

def fix_routes():
    """Fix all route mappings to use correct endpoint names."""
    app = create_app()
    with app.app_context():
        try:
            # Clear existing role mappings first
            db.session.execute(text('DELETE FROM page_route_roles'))
            
            # Get or create Admin category
            admin_category = NavigationCategory.query.filter_by(name='Admin').first()
            if not admin_category:
                admin_category = NavigationCategory(
                    name='Admin',
                    description='Administrative functions',
                    icon='fa-shield-alt',
                    weight=100,
                    created_by='system'
                )
                db.session.add(admin_category)
                db.session.flush()

            # Get admin role
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                print("Error: Admin role not found")
                return

            # Clear existing route mappings
            PageRouteMapping.query.delete()

            # Add core admin routes
            routes_to_add = [
                {
                    'page_name': 'Admin Dashboard',
                    'route': 'admin.index',
                    'icon': 'fa-tachometer-alt',
                    'weight': 0,
                    'category': admin_category,
                    'roles': [admin_role]
                },
                {
                    'page_name': 'Roles',
                    'route': 'admin.roles',
                    'icon': 'fa-user-shield',
                    'weight': 1,
                    'category': admin_category,
                    'roles': [admin_role]
                },
                {
                    'page_name': 'Categories',
                    'route': 'admin.categories',
                    'icon': 'fa-folder',
                    'weight': 2,
                    'category': admin_category,
                    'roles': [admin_role]
                },
                {
                    'page_name': 'Routes',
                    'route': 'admin.routes',
                    'icon': 'fa-link',
                    'weight': 3,
                    'category': admin_category,
                    'roles': [admin_role]
                },
                {
                    'page_name': 'Activity Logs',
                    'route': 'admin.activity_logs',
                    'icon': 'fa-history',
                    'weight': 4,
                    'category': admin_category,
                    'roles': [admin_role]
                }
            ]

            # Add all routes
            for route_data in routes_to_add:
                route = PageRouteMapping(
                    page_name=route_data['page_name'],
                    route=route_data['route'],
                    icon=route_data['icon'],
                    weight=route_data['weight'],
                    category_id=route_data['category'].id if route_data['category'] else None
                )
                route.allowed_roles.extend(route_data['roles'])
                db.session.add(route)

            db.session.commit()
            print("Successfully fixed all route mappings")
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing routes: {str(e)}")

if __name__ == '__main__':
    fix_routes()
