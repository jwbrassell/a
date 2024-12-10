"""Fix oncall route mappings."""

import click
from flask.cli import with_appcontext
from app.models import PageRouteMapping, Role, NavigationCategory
from app import db
from sqlalchemy import text, or_

@click.command('fix-oncall-routes')
@with_appcontext
def fix_oncall_routes():
    """Fix oncall route mappings in the database."""
    # Get roles
    admin_role = Role.query.filter_by(name='admin').first()
    demo_role = Role.query.filter_by(name='demo').first()
    
    if not admin_role or not demo_role:
        print("Required roles not found")
        return
        
    try:
        # Get or create Operations category
        category = NavigationCategory.query.filter_by(name='Operations').first()
        if not category:
            category = NavigationCategory(
                name='Operations',
                description='Operational tools and utilities',
                icon='fa-tools',
                weight=50,
                created_by='system'
            )
            db.session.add(category)
            db.session.commit()
        
        # Remove any existing oncall mappings and their role associations
        # Including any incorrect mappings in the main blueprint
        existing_mappings = PageRouteMapping.query.filter(
            or_(
                PageRouteMapping.route.like('oncall%'),
                PageRouteMapping.route.like('main.oncall%'),
                PageRouteMapping.route.like('/oncall/%')  # Also catch URL-style routes
            )
        ).all()
        
        for mapping in existing_mappings:
            # Clear role associations
            mapping.allowed_roles = []
            db.session.delete(mapping)
        
        db.session.commit()
        
        # Create new mappings - only for routes that should appear in navigation
        routes = [
            {
                'route': 'oncall.index',
                'page_name': 'On-Call Schedule',
                'icon': 'fa-calendar-alt',
                'roles': [admin_role, demo_role],
                'weight': 100,
                'show_in_navbar': True
            },
            {
                'route': 'oncall.manage_teams',
                'page_name': 'Manage Teams',
                'icon': 'fa-users',
                'roles': [admin_role],
                'weight': 101,
                'show_in_navbar': True
            },
            {
                'route': 'oncall.upload_oncall',
                'page_name': 'Upload Schedule',
                'icon': 'fa-upload',
                'roles': [admin_role],
                'weight': 102,
                'show_in_navbar': True
            }
            # export_schedule route removed from navigation since it requires parameters
        ]
        
        for route_data in routes:
            mapping = PageRouteMapping(
                route=route_data['route'],
                page_name=route_data['page_name'],
                icon=route_data['icon'],
                weight=route_data['weight'],
                category_id=category.id,  # Assign to Operations category
                show_in_navbar=route_data['show_in_navbar']
            )
            mapping.allowed_roles.extend(route_data['roles'])
            db.session.add(mapping)
            
        # Fix any dispatch routes that use URL format
        dispatch_mappings = PageRouteMapping.query.filter(
            PageRouteMapping.route.like('/dispatch/%')
        ).all()
        
        for mapping in dispatch_mappings:
            # Convert URL format to endpoint format
            new_route = mapping.route.lstrip('/').replace('/', '.')
            mapping.route = new_route
            db.session.add(mapping)
            
        db.session.commit()
        print("Successfully updated oncall route mappings")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating route mappings: {str(e)}")
        raise
