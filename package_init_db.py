from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.models.permissions import Action
from datetime import datetime

def package_init_database():
    # Use the minimal app
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default actions
        default_actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access')
        ]
        
        for name, method, desc in default_actions:
            if not Action.query.filter_by(name=name).first():
                action = Action(name=name, method=method, description=desc)
                db.session.add(action)
        
        # Create admin role
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(
                name='Administrator',
                description='Full system access',
                is_system_role=True
            )
            db.session.add(admin_role)
        
        # Create initial admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_active=True
            )
            admin_user.set_password('admin')
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
        
        try:
            db.session.commit()
            print("Package database initialized successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing package database: {e}")
            return False

if __name__ == '__main__':
    package_init_database()
