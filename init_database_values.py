from app import create_app, db
from app.models import Role, PageRouteMapping, NavigationCategory, User
from datetime import datetime
from sqlalchemy import text

def init_database():
    """Initialize the database by creating all tables"""
    print("\nInitializing database...")
    db.create_all()
    print("Database tables created successfully")

def show_database_info():
    """Display current database information"""
    print("\n=== Current Database Information ===")
    
    # Show all tables
    print("\nDatabase Tables:")
    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    for row in result:
        print(f"- {row[0]}")
    
    # Show roles and their users
    print("\nCurrent Roles and Users:")
    roles = Role.query.all()
    for role in roles:
        users = [user.username for user in role.users]
        print(f"- {role.name}: {', '.join(users) if users else 'No users'}")
    
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
    roles = {}
    for role_data in default_roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Created '{role_data['name']}' role")
        roles[role_data['name']] = role
    db.session.commit()
    return roles

def assign_default_roles():
    """Assign appropriate roles to mock LDAP users"""
    print("\nAssigning default roles to users...")
    
    # Get roles
    admin_role = Role.query.filter_by(name='admin').first()
    user_role = Role.query.filter_by(name='user').first()
    manager_role = Role.query.filter_by(name='manager').first()
    
    # Role assignments
    role_assignments = {
        'admin': [admin_role, user_role],
        'manager': [manager_role, user_role],
        'developer': [user_role],
        'support': [user_role],
        'operator': [user_role],
        'security': [user_role],
        'netadmin': [user_role],
        'devops': [user_role],
        'helpdesk': [user_role],
        'demo': [user_role]
    }
    
    # Create and assign roles to users
    for username, roles in role_assignments.items():
        user = User.query.filter_by(username=username).first()
        if not user:
            # Create user if doesn't exist
            user = User(
                username=username,
                employee_number=f"EMP{username.upper()}",
                name=username.title(),
                email=f"{username}@example.com",
                vzid=username,
                password="test123"
            )
            db.session.add(user)
        
        # Clear existing roles
        user.roles = []
        # Assign new roles
        for role in roles:
            if role not in user.roles:
                user.roles.append(role)
        print(f"Assigned roles to {username}: {', '.join(role.name for role in roles)}")
    
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
            'name': 'Admin',
            'description': 'Administrative features',
            'icon': 'fa-shield-alt',
            'weight': 5,
            'created_by': 'system'
        }
    ]
    
    print("\nEnsuring navigation categories exist...")
    categories = {}
    for cat_data in default_categories:
        category = NavigationCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = NavigationCategory(**cat_data)
            db.session.add(category)
            print(f"Created '{cat_data['name']}' category")
        categories[cat_data['name']] = category
    db.session.commit()
    return categories

def setup_route_permissions():
    """Set up route permissions - admin routes restricted, others accessible"""
    print("\nSetting up route permissions...")
    admin_role = Role.query.filter_by(name='admin').first()
    admin_category = NavigationCategory.query.filter_by(name='Admin').first()
    
    # Admin routes with their configurations
    admin_routes = [
        {
            'route': 'admin.index',
            'page_name': 'Admin Dashboard',
            'icon': 'fa-tachometer-alt',
            'weight': 0
        },
        {
            'route': 'admin.users',
            'page_name': 'User Management',
            'icon': 'fa-users',
            'weight': 10
        },
        {
            'route': 'admin.roles',
            'page_name': 'Role Management',
            'icon': 'fa-user-shield',
            'weight': 20
        },
        {
            'route': 'admin.categories',
            'page_name': 'Navigation Categories',
            'icon': 'fa-folder',
            'weight': 30
        },
        {
            'route': 'admin.routes',
            'page_name': 'Route Management',
            'icon': 'fa-route',
            'weight': 40
        },
        {
            'route': 'admin.analytics',
            'page_name': 'Analytics',
            'icon': 'fa-chart-line',
            'weight': 50
        },
        {
            'route': 'admin.monitoring',
            'page_name': 'System Monitoring',
            'icon': 'fa-heartbeat',
            'weight': 60
        },
        {
            'route': 'admin.vault_status',
            'page_name': 'Vault Status',
            'icon': 'fa-lock',
            'weight': 70
        }
    ]
    
    # Create route mappings
    for route_data in admin_routes:
        mapping = PageRouteMapping.query.filter_by(route=route_data['route']).first()
        if not mapping:
            mapping = PageRouteMapping(
                route=route_data['route'],
                page_name=route_data['page_name'],
                icon=route_data['icon'],
                weight=route_data['weight'],
                category_id=admin_category.id if admin_category else None,
                created_by='system'
            )
            db.session.add(mapping)
            print(f"Created route mapping for {route_data['route']}")
        
        # Ensure admin role is assigned
        if admin_role not in mapping.allowed_roles:
            mapping.allowed_roles.append(admin_role)
            print(f"Restricted {route_data['route']} to admin role")
    
    db.session.commit()

def main():
    """Main function to initialize database values"""
    app = create_app()
    with app.app_context():
        print("Starting database initialization...")
        
        # Initialize database
        init_database()
        
        # Show initial state
        show_database_info()
        
        # Initialize all default values
        roles = ensure_default_roles()
        categories = ensure_navigation_categories()  # Create navigation categories including Admin
        
        # Assign roles to users
        assign_default_roles()
        
        # Set up route permissions
        setup_route_permissions()
        
        # Show final state
        print("\n=== Final Database State ===")
        show_database_info()

if __name__ == '__main__':
    main()
