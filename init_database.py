from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from datetime import datetime

def init_database():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default roles if they don't exist
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(
                name='Administrator',
                description='Full system access',
                is_system_role=True,
                weight=100,
                created_at=datetime.utcnow(),
                created_by='system',  # String value for created_by
                updated_at=datetime.utcnow(),
                updated_by='system',  # String value for updated_by
                ldap_groups=[],
                auto_sync=False
            )
            db.session.add(admin_role)
            db.session.flush()
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                created_at=datetime.utcnow()
            )
            admin_user.set_password('admin')
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
        
        db.session.commit()
        print("Database initialized successfully")

if __name__ == '__main__':
    init_database()
