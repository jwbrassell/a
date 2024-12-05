from app import db
from app.models import User, Role
from werkzeug.security import generate_password_hash

def init_roles_and_users():
    """Initialize default roles and users."""
    # Create default roles if they don't exist
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(
            name='admin',
            notes='Administrator role with full access',
            icon='fa-user-shield',
            created_by='system'
        )
        db.session.add(admin_role)

    demo_role = Role.query.filter_by(name='demo').first()
    if not demo_role:
        demo_role = Role(
            name='demo',
            notes='Demo user role',
            icon='fa-user',
            created_by='system'
        )
        db.session.add(demo_role)

    # Create default users if they don't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            employee_number='ADMIN001',
            name='Administrator',
            email='admin@example.com',
            vzid='admin',
            roles=[admin_role],
            password='admin123'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)

    demo_user = User.query.filter_by(username='user').first()
    if not demo_user:
        demo_user = User(
            username='user',
            employee_number='USER001',
            name='Demo User',
            email='user@example.com',
            vzid='user',
            roles=[demo_role],
            password='user123'
        )
        demo_user.set_password('user123')
        db.session.add(demo_user)

    try:
        db.session.commit()
        print("Successfully initialized default roles and users")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing defaults: {str(e)}")
