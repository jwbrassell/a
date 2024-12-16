"""Project utility functions."""

from app.models import PageRouteMapping
from app.extensions import db
from app.models import Role, Permission

def can_edit_project(user, project):
    """Check if a user can edit a project based on RBAC permissions.
    
    Args:
        user: The user to check permissions for
        project: The project to check access to
        
    Returns:
        bool: True if user has edit access, False otherwise
    """
    if not user or not project:
        return False
        
    # Admin users always have access
    if any(role.name == 'admin' for role in user.roles):
        return True
        
    # Get the route mapping for the edit project endpoint
    mapping = PageRouteMapping.query.filter_by(route='projects.edit_project').first()
    
    if not mapping:
        # If no mapping exists, default to requiring authentication only
        return True
        
    # Get the set of role names required for this route
    required_roles = {role.name for role in mapping.allowed_roles}
    
    if not required_roles:
        # If no roles are specified, default to requiring authentication only
        return True
        
    # Get the set of user's role names
    user_roles = {role.name for role in user.roles}
    
    # Check if user has any of the required roles
    return bool(required_roles & user_roles)

def route_to_endpoint(route: str) -> str:
    """Convert route name to endpoint name.
    For example: 'index' -> 'projects.index'
             'dashboard' -> 'projects.project_dashboard'
    """
    if not route:
        return ''
    
    # If it's already a fully qualified endpoint (contains a dot), return as is
    if '.' in route:
        return route
        
    # Map common route names to their endpoints
    route_map = {
        'index': 'projects.index',
        'dashboard': 'projects.project_dashboard',
        'kanban': 'projects.project_kanban',
        'calendar': 'projects.project_calendar',
        'timeline': 'projects.project_timeline',
        'settings': 'projects.project_settings',
        'reports': 'projects.project_reports',
        'list': 'projects.list_projects',
        'new': 'projects.new_project',
        'create': 'projects.create_project'
    }
    
    # Return mapped endpoint or default to projects.{route}
    return route_map.get(route, f'projects.{route}')

def init_default_configurations(app):
    """Initialize default configurations for the projects plugin."""
    with app.app_context():
        # Register base permissions
        permissions = [
            ('projects_access', 'Access projects'),
            ('projects_create', 'Create projects'),
            ('projects_edit', 'Edit projects'),
            ('projects_delete', 'Delete projects'),
            ('projects_manage', 'Manage project settings'),
            ('projects_view_all', 'View all projects'),
            ('projects_edit_all', 'Edit all projects')
        ]
        
        for name, description in permissions:
            if not Permission.query.filter_by(name=name).first():
                permission = Permission(
                    name=name, 
                    description=description,
                    created_by='system'  # Set created_by to 'system'
                )
                db.session.add(permission)
        
        # Assign permissions to roles
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            for name, _ in permissions:
                perm = Permission.query.filter_by(name=name).first()
                if perm and perm not in admin_role.permissions:
                    admin_role.add_permission(perm)
        
        # Commit changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error initializing project configurations: {str(e)}")
            raise

def register_commands(app):
    """Register CLI commands for the projects plugin."""
    @app.cli.group()
    def projects():
        """Projects plugin commands."""
        pass

    @projects.command()
    def init():
        """Initialize project data."""
        init_default_configurations(app)
        print("Initialized project configurations.")
