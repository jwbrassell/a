from app import create_app, db
from app.models import User, Role
from app.models.permission import Permission
from datetime import datetime
import os

def init_db():
    """Initialize the database with default users and roles."""
    # Create app with session handling disabled initially
    app = create_app(skip_session=True)
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Initialize default permissions
        Permission.initialize_default_permissions()
        
        # Create roles if they don't exist
        roles = {
            'admin': 'Administrator role with full access',
            'manager': 'Team manager role with elevated access',
            'developer': 'Developer role with project access',
            'support': 'Support role with help desk access',
            'operator': 'Operations role with system access',
            'security': 'Security role with security monitoring access',
            'netadmin': 'Network administrator role',
            'devops': 'DevOps role with deployment access',
            'helpdesk': 'Help desk support role',
            'user': 'Standard user role'
        }
        
        created_roles = {}
        for role_name, description in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=description,
                    created_by='system',
                    created_at=datetime.utcnow(),
                    is_system_role=True  # Mark as system role for protection
                )
                db.session.add(role)
            created_roles[role_name] = role
        
        # Ensure admin role has all permissions
        all_permissions = Permission.query.all()
        if created_roles['admin']:
            created_roles['admin'].permissions = all_permissions
            
        # Set up basic permissions for user role
        if created_roles['user']:
            user_permissions = Permission.query.filter(
                Permission.name.in_(['user_profile_access', 'user_settings_access'])
            ).all()
            created_roles['user'].permissions = user_permissions
        
        # Create default users from mock LDAP
        default_users = [
            {
                'username': 'admin',
                'employee_number': 'EMP001',
                'name': 'Admin User',
                'email': 'admin@example.com',
                'vzid': 'VZ001',
                'roles': ['admin', 'user']
            },
            {
                'username': 'manager',
                'employee_number': 'EMP002',
                'name': 'Team Manager',
                'email': 'manager@example.com',
                'vzid': 'VZ002',
                'roles': ['manager', 'user']
            },
            {
                'username': 'developer',
                'employee_number': 'EMP003',
                'name': 'Development User',
                'email': 'developer@example.com',
                'vzid': 'VZ003',
                'roles': ['developer', 'user']
            },
            {
                'username': 'support',
                'employee_number': 'EMP004',
                'name': 'Support User',
                'email': 'support@example.com',
                'vzid': 'VZ004',
                'roles': ['support', 'user']
            },
            {
                'username': 'operator',
                'employee_number': 'EMP005',
                'name': 'Operations User',
                'email': 'operator@example.com',
                'vzid': 'VZ005',
                'roles': ['operator', 'user']
            },
            {
                'username': 'security',
                'employee_number': 'EMP006',
                'name': 'Security User',
                'email': 'security@example.com',
                'vzid': 'VZ006',
                'roles': ['security', 'user']
            },
            {
                'username': 'netadmin',
                'employee_number': 'EMP007',
                'name': 'Network Admin User',
                'email': 'netadmin@example.com',
                'vzid': 'VZ007',
                'roles': ['netadmin', 'user']
            },
            {
                'username': 'devops',
                'employee_number': 'EMP008',
                'name': 'DevOps User',
                'email': 'devops@example.com',
                'vzid': 'VZ008',
                'roles': ['devops', 'user']
            },
            {
                'username': 'helpdesk',
                'employee_number': 'EMP009',
                'name': 'Helpdesk User',
                'email': 'helpdesk@example.com',
                'vzid': 'VZ009',
                'roles': ['helpdesk', 'user']
            },
            {
                'username': 'demo',
                'employee_number': 'EMP010',
                'name': 'Demo User',
                'email': 'demo@example.com',
                'vzid': 'VZ010',
                'roles': ['user']
            }
        ]
        
        # Create users
        for user_info in default_users:
            user = User.query.filter_by(username=user_info['username']).first()
            if not user:
                user = User(
                    username=user_info['username'],
                    employee_number=user_info['employee_number'],
                    name=user_info['name'],
                    email=user_info['email'],
                    vzid=user_info['vzid'],
                    roles=[created_roles[role] for role in user_info['roles']]
                )
                user.set_password('test123')  # Set default password
                db.session.add(user)
        
        # Commit the changes
        db.session.commit()
        
        print("Database initialized with default users and roles.")
        print("\nAvailable users (all with password 'test123'):")
        for user_info in default_users:
            print(f"Username: {user_info['username']}")
            print(f"Name: {user_info['name']}")
            print(f"Roles: {', '.join(user_info['roles'])}")
            print("-" * 50)

if __name__ == '__main__':
    init_db()
