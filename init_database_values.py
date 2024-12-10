from app import create_app, db
from app.models import Role, PageRouteMapping, NavigationCategory, page_route_roles
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

def ensure_user_role_exists():
    """Ensure the 'user' role exists"""
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        print("\nCreating 'user' role...")
        user_role = Role(
            name='user',
            notes='Default user role',
            icon='fa-user',
            created_by='system'
        )
        db.session.add(user_role)
        db.session.commit()
        print("'user' role created successfully")
    else:
        print("\n'user' role already exists")

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
        
        # Ensure user role exists
        ensure_user_role_exists()
        
        # Make routes accessible by removing role restrictions
        make_routes_accessible()
        
        # Show final state
        print("\n=== Final Database State ===")
        show_database_info()

if __name__ == '__main__':
    main()
