from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.models.permissions import Action
from datetime import datetime

def init_database():
    app = create_app('development')  # Explicitly use development config
    with app.app_context():
        # Create default actions
        default_actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access'),
            ('list', 'GET', 'List access'),
            ('create', 'POST', 'Create access'),
            ('edit', 'PUT', 'Edit access'),
            ('remove', 'DELETE', 'Remove access')
        ]
        
        for name, method, desc in default_actions:
            if not Action.query.filter_by(name=name, method=method).first():
                action = Action(
                    name=name,
                    method=method,
                    description=desc,
                    created_by='system',
                    created_at=datetime.utcnow()
                )
                db.session.add(action)
        
        db.session.flush()
        
        # Create default permissions if they don't exist
        default_permissions = [
            ('admin_access', 'Full administrative access', 'admin'),
            ('user_manage', 'User management access', 'admin'),
            ('role_manage', 'Role management access', 'admin'),
            ('system_config', 'System configuration access', 'admin'),
        ]
        
        for name, desc, category in default_permissions:
            if not Permission.query.filter_by(name=name).first():
                permission = Permission(
                    name=name,
                    description=desc,
                    category=category,
                    created_by='system',
                    created_at=datetime.utcnow(),
                    updated_by='system',
                    updated_at=datetime.utcnow()
                )
                # Add all actions to admin_access permission
                if name == 'admin_access':
                    permission.actions = Action.query.all()
                db.session.add(permission)
        
        db.session.flush()
        
        # Create default roles if they don't exist
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(
                name='Administrator',
                description='Full system access',
                is_system_role=True,
                weight=100,
                created_at=datetime.utcnow(),
                created_by='system',
                updated_at=datetime.utcnow(),
                updated_by='system',
                ldap_groups=[],
                auto_sync=False
            )
            # Add all permissions to admin role
            admin_role.permissions = Permission.query.all()
            db.session.add(admin_role)
            db.session.flush()
        
        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                created_at=datetime.utcnow(),
                is_active=True
            )
            admin_user.set_password('admin')
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
        
        # Initialize project statuses
        try:
            from app.blueprints.projects.models import ProjectStatus
            if not ProjectStatus.query.first():
                print("Creating default project statuses")
                statuses = [
                    ('Not Started', '#dc3545'),  # Red
                    ('In Progress', '#ffc107'),  # Yellow
                    ('On Hold', '#6c757d'),      # Gray
                    ('Completed', '#28a745'),    # Green
                    ('Cancelled', '#343a40')     # Dark
                ]
                for name, color in statuses:
                    status = ProjectStatus(
                        name=name,
                        color=color,
                        created_by='system',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(status)
        except Exception as e:
            print(f"Note: Project status table not available: {e}")

        # Initialize project priorities
        try:
            from app.blueprints.projects.models import ProjectPriority
            if not ProjectPriority.query.first():
                print("Creating default project priorities")
                priorities = [
                    ('Low', '#28a745'),      # Green
                    ('Medium', '#ffc107'),   # Yellow
                    ('High', '#dc3545'),     # Red
                    ('Critical', '#9c27b0')  # Purple
                ]
                for name, color in priorities:
                    priority = ProjectPriority(
                        name=name,
                        color=color,
                        created_by='system',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(priority)
        except Exception as e:
            print(f"Note: Project priority table not available: {e}")

        try:
            db.session.commit()
            print("Database initialized successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {e}")
            return False

if __name__ == '__main__':
    init_database()
