from flask import current_app
from app.utils.enhanced_rbac import register_permission
from app.models.permission import Permission

def register_blueprint(app):
    """Register the database_reports blueprint and set up required permissions"""
    from . import bp
    
    # Register the blueprint
    app.register_blueprint(bp)
    
    # Create required permissions
    permissions = [
        {
            'name': 'manage_database_connections',
            'description': 'Ability to create and manage database connections'
        },
        {
            'name': 'create_reports',
            'description': 'Ability to create new database reports'
        },
        {
            'name': 'edit_reports',
            'description': 'Ability to edit existing database reports'
        },
        {
            'name': 'view_reports',
            'description': 'Ability to view database reports'
        }
    ]
    
    # Create permissions if they don't exist
    for permission in permissions:
        register_permission(
            permission['name'],
            permission['description']
        )
    
    # Add menu items
    if hasattr(app, 'admin_menu'):
        app.admin_menu.append({
            'name': 'Database Reports',
            'icon': 'fas fa-database',
            'route': 'database_reports.index',
            'items': [
                {
                    'name': 'All Reports',
                    'route': 'database_reports.index'
                },
                {
                    'name': 'New Report',
                    'route': 'database_reports.new_report',
                    'permission': 'create_reports'
                },
                {
                    'name': 'Manage Connections',
                    'route': 'database_reports.list_connections',
                    'permission': 'manage_database_connections'
                }
            ]
        })

def init_app(app):
    """Initialize the database_reports blueprint"""
    with app.app_context():
        register_blueprint(app)
