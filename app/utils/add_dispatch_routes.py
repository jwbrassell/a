"""Add dispatch routes to navigation."""
from app.extensions import db
from app.models.navigation import NavigationCategory, PageRouteMapping
from app.models.role import Role
from app.models.permission import Permission

def add_dispatch_routes():
    """Add dispatch routes to navigation."""
    # Get admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("Error: Admin role not found")
        return False

    try:
        # Create dispatch admin permission if it doesn't exist
        dispatch_permission = Permission.get_by_name('admin_dispatch_access')
        if not dispatch_permission:
            dispatch_permission = Permission.create_permission(
                name='admin_dispatch_access',
                description='Access dispatch administration',
                category='admin',
                created_by='system'
            )
            # Add permission to admin role
            if dispatch_permission not in admin_role.permissions:
                admin_role.permissions.append(dispatch_permission)
                db.session.commit()

        # Create Dispatch category
        dispatch_category = NavigationCategory.query.filter_by(name='Dispatch').first()
        if not dispatch_category:
            dispatch_category = NavigationCategory(
                name='Dispatch',
                icon='fas fa-envelope',
                description='Email dispatch system',
                weight=50,  # Adjust as needed
                created_by='system'
            )
            db.session.add(dispatch_category)
            db.session.flush()

        # Add main dispatch route
        dispatch_route = PageRouteMapping.query.filter_by(route='dispatch.dispatch_request').first()
        if not dispatch_route:
            dispatch_route = PageRouteMapping(
                page_name='Dispatch Request',
                route='dispatch.dispatch_request',
                description='Submit dispatch requests',
                icon='fas fa-paper-plane',
                category_id=dispatch_category.id,
                weight=10,
                show_in_navbar=True,
                created_by='system'
            )
            db.session.add(dispatch_route)

        # Add admin settings route
        admin_route = PageRouteMapping.query.filter_by(route='dispatch.admin_settings').first()
        if not admin_route:
            admin_route = PageRouteMapping(
                page_name='Dispatch Settings',
                route='dispatch.admin_settings',
                description='Configure dispatch settings',
                icon='fas fa-cog',
                category_id=dispatch_category.id,
                weight=20,
                show_in_navbar=True,
                created_by='system'
            )
            # Only admins can access settings
            admin_route.allowed_roles.append(admin_role)
            db.session.add(admin_route)

        db.session.commit()
        print("Successfully added dispatch routes and permissions")
        return True

    except Exception as e:
        print(f"Error adding dispatch routes: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from flask import current_app
    with current_app.app_context():
        add_dispatch_routes()
