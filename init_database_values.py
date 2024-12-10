from app import create_app, db
from app.models import Role, PageRouteMapping, NavigationCategory
from app.plugins.projects.models import ProjectStatus, ProjectPriority
from app.plugins.dispatch.models import DispatchTeam, DispatchPriority
from app.plugins.documents.models import DocumentCategory
from app.plugins.oncall.models import Team as OncallTeam
from app.plugins.handoffs.models import HandoffShift
from datetime import datetime
from sqlalchemy import text

def show_database_info():
    """Display current database information"""
    print("\n=== Current Database Information ===")
    
    # Show all tables
    print("\nDatabase Tables:")
    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    for row in result:
        print(f"- {row[0]}")
    
    # Show roles
    print("\nCurrent Roles:")
    roles = Role.query.all()
    for role in roles:
        print(f"- {role.name}")
    
    # Show routes and their access
    print("\nCurrent Routes and Access:")
    routes = PageRouteMapping.query.all()
    for route in routes:
        allowed_roles = [role.name for role in route.allowed_roles]
        print(f"- {route.route} -> {', '.join(allowed_roles) if allowed_roles else 'No roles assigned (publicly accessible)'}")

def ensure_default_roles():
    """Ensure default roles exist"""
    default_roles = [
        {
            'name': 'admin',
            'notes': 'Administrator role with full access',
            'icon': 'fa-shield-alt',
            'created_by': 'system'
        },
        {
            'name': 'user',
            'notes': 'Default user role',
            'icon': 'fa-user',
            'created_by': 'system'
        },
        {
            'name': 'manager',
            'notes': 'Manager role with elevated access',
            'icon': 'fa-user-tie',
            'created_by': 'system'
        }
    ]
    
    print("\nEnsuring default roles exist...")
    for role_data in default_roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Created '{role_data['name']}' role")
    db.session.commit()

def ensure_navigation_categories():
    """Ensure default navigation categories exist"""
    default_categories = [
        {
            'name': 'Core',
            'description': 'Core application features',
            'icon': 'fa-home',
            'weight': 0,
            'created_by': 'system'
        },
        {
            'name': 'Projects',
            'description': 'Project management features',
            'icon': 'fa-project-diagram',
            'weight': 10,
            'created_by': 'system'
        },
        {
            'name': 'Operations',
            'description': 'Operational features',
            'icon': 'fa-cogs',
            'weight': 20,
            'created_by': 'system'
        },
        {
            'name': 'Documentation',
            'description': 'Documentation and resources',
            'icon': 'fa-book',
            'weight': 30,
            'created_by': 'system'
        }
    ]
    
    print("\nEnsuring navigation categories exist...")
    for cat_data in default_categories:
        category = NavigationCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = NavigationCategory(**cat_data)
            db.session.add(category)
            print(f"Created '{cat_data['name']}' category")
    db.session.commit()

def ensure_project_statuses():
    """Ensure default project statuses exist"""
    default_statuses = [
        {'name': 'Not Started', 'color': '#dc3545', 'created_by': 'system'},
        {'name': 'In Progress', 'color': '#ffc107', 'created_by': 'system'},
        {'name': 'On Hold', 'color': '#6c757d', 'created_by': 'system'},
        {'name': 'Completed', 'color': '#28a745', 'created_by': 'system'},
        {'name': 'Cancelled', 'color': '#343a40', 'created_by': 'system'}
    ]
    
    print("\nEnsuring project statuses exist...")
    for status_data in default_statuses:
        status = ProjectStatus.query.filter_by(name=status_data['name']).first()
        if not status:
            status = ProjectStatus(**status_data)
            db.session.add(status)
            print(f"Created '{status_data['name']}' status")
    db.session.commit()

def ensure_project_priorities():
    """Ensure default project priorities exist"""
    default_priorities = [
        {'name': 'Low', 'color': '#28a745', 'created_by': 'system'},
        {'name': 'Medium', 'color': '#ffc107', 'created_by': 'system'},
        {'name': 'High', 'color': '#dc3545', 'created_by': 'system'},
        {'name': 'Critical', 'color': '#9c27b0', 'created_by': 'system'}
    ]
    
    print("\nEnsuring project priorities exist...")
    for priority_data in default_priorities:
        priority = ProjectPriority.query.filter_by(name=priority_data['name']).first()
        if not priority:
            priority = ProjectPriority(**priority_data)
            db.session.add(priority)
            print(f"Created '{priority_data['name']}' priority")
    db.session.commit()

def ensure_dispatch_defaults():
    """Ensure default dispatch teams and priorities exist"""
    # Teams
    default_teams = [
        {'name': 'Network', 'email': 'network@example.com', 'description': 'Network team'},
        {'name': 'Security', 'email': 'security@example.com', 'description': 'Security team'},
        {'name': 'Systems', 'email': 'systems@example.com', 'description': 'Systems team'}
    ]
    
    print("\nEnsuring dispatch teams exist...")
    for team_data in default_teams:
        team = DispatchTeam.query.filter_by(name=team_data['name']).first()
        if not team:
            team = DispatchTeam(**team_data)
            db.session.add(team)
            print(f"Created '{team_data['name']}' team")
    
    # Priorities
    default_priorities = [
        {'name': 'P1', 'description': 'Critical', 'color': '#dc3545', 'icon': 'fa-exclamation-circle'},
        {'name': 'P2', 'description': 'High', 'color': '#ffc107', 'icon': 'fa-exclamation-triangle'},
        {'name': 'P3', 'description': 'Medium', 'color': '#17a2b8', 'icon': 'fa-info-circle'},
        {'name': 'P4', 'description': 'Low', 'color': '#28a745', 'icon': 'fa-check-circle'}
    ]
    
    print("\nEnsuring dispatch priorities exist...")
    for priority_data in default_priorities:
        priority = DispatchPriority.query.filter_by(name=priority_data['name']).first()
        if not priority:
            priority = DispatchPriority(**priority_data)
            db.session.add(priority)
            print(f"Created '{priority_data['name']}' priority")
    
    db.session.commit()

def ensure_document_categories():
    """Ensure default document categories exist"""
    default_categories = [
        {'name': 'Procedures', 'description': 'Standard operating procedures'},
        {'name': 'Guides', 'description': 'How-to guides and tutorials'},
        {'name': 'Policies', 'description': 'Company policies and guidelines'},
        {'name': 'Templates', 'description': 'Document templates'}
    ]
    
    print("\nEnsuring document categories exist...")
    for cat_data in default_categories:
        category = DocumentCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = DocumentCategory(**cat_data)
            db.session.add(category)
            print(f"Created '{cat_data['name']}' category")
    db.session.commit()

def ensure_oncall_teams():
    """Ensure default oncall teams exist"""
    default_teams = [
        {'name': 'Network Operations', 'color': '#007bff'},
        {'name': 'Security Operations', 'color': '#dc3545'},
        {'name': 'Systems Operations', 'color': '#28a745'}
    ]
    
    print("\nEnsuring oncall teams exist...")
    for team_data in default_teams:
        team = OncallTeam.query.filter_by(name=team_data['name']).first()
        if not team:
            team = OncallTeam(**team_data)
            db.session.add(team)
            print(f"Created '{team_data['name']}' team")
    db.session.commit()

def ensure_handoff_shifts():
    """Ensure default handoff shifts exist"""
    default_shifts = [
        {'name': 'Morning', 'description': '6:00 AM - 2:00 PM'},
        {'name': 'Afternoon', 'description': '2:00 PM - 10:00 PM'},
        {'name': 'Night', 'description': '10:00 PM - 6:00 AM'}
    ]
    
    print("\nEnsuring handoff shifts exist...")
    for shift_data in default_shifts:
        shift = HandoffShift.query.filter_by(name=shift_data['name']).first()
        if not shift:
            shift = HandoffShift(**shift_data)
            db.session.add(shift)
            print(f"Created '{shift_data['name']}' shift")
    db.session.commit()

def make_routes_accessible():
    """Make all routes accessible by default by removing role restrictions"""
    print("\nMaking all routes accessible by default...")
    routes = PageRouteMapping.query.all()
    modified = 0
    
    for route in routes:
        if route.allowed_roles:
            # Clear all role restrictions
            route.allowed_roles = []
            modified += 1
            print(f"Removing role restrictions from route: {route.route}")
    
    if modified:
        db.session.commit()
        print(f"Removed role restrictions from {modified} routes")
    else:
        print("All routes are already accessible")

def main():
    """Main function to initialize database values"""
    app = create_app()
    with app.app_context():
        print("Starting database initialization...")
        
        # Show initial state
        show_database_info()
        
        # Initialize all default values
        ensure_default_roles()
        ensure_navigation_categories()
        ensure_project_statuses()
        ensure_project_priorities()
        ensure_dispatch_defaults()
        ensure_document_categories()
        ensure_oncall_teams()
        ensure_handoff_shifts()
        
        # Make routes accessible by removing role restrictions
        make_routes_accessible()
        
        # Show final state
        print("\n=== Final Database State ===")
        show_database_info()

if __name__ == '__main__':
    main()
