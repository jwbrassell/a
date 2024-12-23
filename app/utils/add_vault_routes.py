"""Add vault management routes to navigation."""
from app.models import NavigationCategory, PageRouteMapping, Role
from app.extensions import db
from app.utils.route_manager import route_to_endpoint

def add_vault_routes():
    """Add vault management routes to navigation."""
    try:
        # Get or create Admin Tools category
        admin_category = NavigationCategory.query.filter_by(name='Admin Tools').first()
        if not admin_category:
            admin_category = NavigationCategory(
                name='Admin Tools',
                icon='fas fa-tools',
                description='Administrative tools and settings',
                weight=1000,  # High weight to appear at bottom
                created_by='system'
            )
            db.session.add(admin_category)
            db.session.flush()

        # Get Administrator role
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            raise ValueError("Administrator role not found")

        # Add Vault Management route
        vault_route = PageRouteMapping.query.filter_by(route='/admin/vault').first()
        if not vault_route:
            vault_route = PageRouteMapping(
                page_name='Vault Management',
                route='/admin/vault',
                description='Manage Vault secrets, policies, and monitor performance',
                icon='fas fa-shield-alt',
                weight=50,
                category_id=admin_category.id,
                show_in_navbar=True,
                created_by='system'
            )
            vault_route.allowed_roles.append(admin_role)
            db.session.add(vault_route)

        db.session.commit()
        print("Successfully added vault routes to navigation")
        return True

    except Exception as e:
        print(f"Error adding vault routes: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        add_vault_routes()
