"""Create admin user for testing."""

import eventlet
eventlet.monkey_patch()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.utils.enhanced_rbac import register_permission

def create_admin_user():
    """Create admin user and role with necessary permissions."""
    app = create_app('development')
    
    with app.app_context():
        # Create admin role if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator role with full access',
                created_by='system'  # Added this line
            )
            db.session.add(admin_role)
        
        # Register monitoring permissions
        monitoring_permission = register_permission(
            'admin_monitoring_access',
            'Access to admin monitoring features',
            actions=['read', 'write']
        )
        
        # Add permission to admin role
        if monitoring_permission not in admin_role.permissions:
            admin_role.permissions.append(monitoring_permission)
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                name='Administrator',
                email='admin@example.com'
            )
            admin_user.set_password('admin')  # Set default password
            db.session.add(admin_user)
        
        # Ensure admin user has admin role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
        
        db.session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin")

if __name__ == '__main__':
    create_admin_user()
