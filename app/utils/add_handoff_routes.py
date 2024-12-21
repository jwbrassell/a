"""Add handoff routes to navigation."""
from app.extensions import db
from app.models.navigation import NavigationCategory, PageRouteMapping
from app.models.role import Role
from app.models.permission import Permission

def add_handoff_routes():
    """Add handoff routes to navigation."""
    # Get admin role
    admin_role = Role.query.filter_by(name='Administrator').first()
    if not admin_role:
        print("Error: Admin role not found")
        return False

    try:
        # Create handoff admin permission if it doesn't exist
        admin_permission = Permission.get_by_name('admin_handoffs_access')
        if not admin_permission:
            admin_permission = Permission.create_permission(
                name='admin_handoffs_access',
                description='Access handoff administration',
                category='admin',
                created_by='system'
            )
            # Add permission to admin role
            if admin_permission not in admin_role.permissions:
                admin_role.permissions.append(admin_permission)
                db.session.commit()

        # Create metrics permission if it doesn't exist
        metrics_permission = Permission.get_by_name('view_metrics')
        if not metrics_permission:
            metrics_permission = Permission.create_permission(
                name='view_metrics',
                description='View handoff metrics',
                category='metrics',
                created_by='system'
            )
            # Add permission to admin role
            if metrics_permission not in admin_role.permissions:
                admin_role.permissions.append(metrics_permission)
                db.session.commit()

        # Create Handoffs category
        handoffs_category = NavigationCategory.query.filter_by(name='Handoffs').first()
        if not handoffs_category:
            handoffs_category = NavigationCategory(
                name='Handoffs',
                icon='fas fa-exchange-alt',
                description='Handoff management system',
                weight=60,  # After Dispatch
                created_by='system'
            )
            db.session.add(handoffs_category)
            db.session.flush()

        # Add main handoffs route
        main_route = PageRouteMapping.query.filter_by(route='handoffs.index').first()
        if not main_route:
            main_route = PageRouteMapping(
                page_name='Handoffs',
                route='handoffs.index',
                description='View and manage handoffs',
                icon='fas fa-list',
                category_id=handoffs_category.id,
                weight=10,
                show_in_navbar=True,
                created_by='system'
            )
            db.session.add(main_route)

        # Add create handoff route
        create_route = PageRouteMapping.query.filter_by(route='handoffs.create').first()
        if not create_route:
            create_route = PageRouteMapping(
                page_name='Create Handoff',
                route='handoffs.create',
                description='Create a new handoff',
                icon='fas fa-plus',
                category_id=handoffs_category.id,
                weight=20,
                show_in_navbar=True,
                created_by='system'
            )
            db.session.add(create_route)

        # Add metrics route
        metrics_route = PageRouteMapping.query.filter_by(route='handoffs.metrics').first()
        if not metrics_route:
            metrics_route = PageRouteMapping(
                page_name='Handoff Metrics',
                route='handoffs.metrics',
                description='View handoff metrics and statistics',
                icon='fas fa-chart-bar',
                category_id=handoffs_category.id,
                weight=30,
                show_in_navbar=True,
                created_by='system'
            )
            # Only users with metrics permission can access
            metrics_route.allowed_roles.append(admin_role)
            db.session.add(metrics_route)

        # Add admin settings route
        admin_route = PageRouteMapping.query.filter_by(route='handoffs.admin_settings').first()
        if not admin_route:
            admin_route = PageRouteMapping(
                page_name='Handoff Settings',
                route='handoffs.admin_settings',
                description='Configure handoff settings',
                icon='fas fa-cog',
                category_id=handoffs_category.id,
                weight=40,
                show_in_navbar=True,
                created_by='system'
            )
            # Only admins can access settings
            admin_route.allowed_roles.append(admin_role)
            db.session.add(admin_route)

        db.session.commit()
        print("Successfully added handoff routes and permissions")
        return True

    except Exception as e:
        print(f"Error adding handoff routes: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from flask import current_app
    with current_app.app_context():
        add_handoff_routes()
