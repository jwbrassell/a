from app.extensions import db
from app import create_app
from app.models import NavigationCategory, PageRouteMapping, Role

def add_project_routes():
    """Add project routes to navigation under Management category."""
    app = create_app()
    with app.app_context():
        # Get or create the Management category
        mgmt_category = NavigationCategory.query.filter_by(name='Management').first()
        if not mgmt_category:
            mgmt_category = NavigationCategory(
                name='Management',
                description='Project and resource management',
                icon='fa-tasks',
                weight=50,  # Middle weight
                created_by='system'
            )
            db.session.add(mgmt_category)
            db.session.flush()  # Flush to get the category ID

        # Get user role
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(
                name='user',
                notes='Basic user role',
                icon='fa-user',
                created_by='system'
            )
            db.session.add(user_role)
            db.session.flush()

        # Add projects route if it doesn't exist
        projects_route = PageRouteMapping.query.filter_by(route='projects.index').first()
        if not projects_route:
            projects_route = PageRouteMapping(
                page_name='Projects',
                route='projects.index',
                icon='fa-project-diagram',
                weight=10,  # High priority in Management category
                category_id=mgmt_category.id,
                show_in_navbar=True
            )
            projects_route.allowed_roles.append(user_role)
            db.session.add(projects_route)

        try:
            db.session.commit()
            print("Successfully added project routes")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding project routes: {str(e)}")

if __name__ == '__main__':
    add_project_routes()
