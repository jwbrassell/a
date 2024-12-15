from app import create_app, db
from app.models import User, Role
from app.models.permission import Permission
from datetime import datetime

def init_db():
    """Initialize the database with default admin user and roles."""
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Initialize default permissions
        Permission.initialize_default_permissions()
        
        # Create roles if they don't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator role with full access',
                created_by='system',
                created_at=datetime.utcnow(),
                is_system_role=True  # Mark as system role for protection
            )
            db.session.add(admin_role)

        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(
                name='user',
                description='Standard user role',
                created_by='system',
                created_at=datetime.utcnow(),
                is_system_role=True  # Mark as system role for protection
            )
            db.session.add(user_role)
        
        # Ensure admin role has all permissions
        all_permissions = Permission.query.all()
        if admin_role:
            admin_role.permissions = all_permissions
            
        # Ensure user role has basic permissions
        if user_role:
            user_permissions = Permission.query.filter(
                Permission.name.in_(['user_profile_access', 'user_settings_access'])
            ).all()
            user_role.permissions = user_permissions
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                employee_number='ADMIN001',
                name='Administrator',
                email='admin@example.com',
                vzid='ADMIN',
                roles=[admin_role, user_role]
            )
            admin_user.set_password('admin')  # Set password using the proper method
            db.session.add(admin_user)
        
        # Commit the changes
        db.session.commit()
        
        print("Database initialized with admin user and roles.")
        print("Admin credentials:")
        print("Username: admin")
        print("Password: admin")
        print("\nAdmin role has been granted all permissions.")

if __name__ == '__main__':
    init_db()
