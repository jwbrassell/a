from app import create_app, db
from app.models import User, Role
from datetime import datetime

def init_db():
    """Initialize the database with default admin user and roles."""
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create roles if they don't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                notes='Administrator role with full access',
                icon='fa-user-shield',
                created_by='system',
                created_at=datetime.utcnow()
            )
            db.session.add(admin_role)

        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(
                name='user',
                notes='Standard user role',
                icon='fa-user',
                created_by='system',
                created_at=datetime.utcnow()
            )
            db.session.add(user_role)
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                employee_number='ADMIN001',
                name='Administrator',
                email='admin@example.com',
                vzid='ADMIN',
                roles=[admin_role, user_role],
                password='admin'  # This will be hashed by the model
            )
            db.session.add(admin_user)
        
        # Commit the changes
        db.session.commit()
        
        print("Database initialized with admin user and roles.")
        print("Admin credentials:")
        print("Username: admin")
        print("Password: admin")

if __name__ == '__main__':
    init_db()
