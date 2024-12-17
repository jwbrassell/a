#!/usr/bin/env python3
"""
Setup script to initialize the application.
This script will:
1. Create database and tables
2. Initialize permissions
3. Initialize role templates
4. Set up admin user with full access
5. Start the Flask app
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from flask import Flask
from app.extensions import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define required admin permissions with their required actions
ADMIN_PERMISSIONS = {
    'admin_dashboard_access': {
        'description': 'Access to admin dashboard',
        'actions': ['read']
    },
    'admin_routes_access': {
        'description': 'Access to route management',
        'actions': ['read', 'write', 'update', 'delete']
    },
    'admin_analytics_access': {
        'description': 'Access to analytics dashboard',
        'actions': ['read']
    },
    'admin_vault_access': {
        'description': 'Access to vault management',
        'actions': ['read']
    },
    'admin_users_access': {
        'description': 'Access to user management',
        'actions': ['read', 'write', 'update', 'delete']
    },
    'admin_logs_access': {
        'description': 'Access to system logs',
        'actions': ['read']
    }
}

def create_app():
    """Create a Flask app for database setup."""
    app = Flask(__name__)
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{os.path.join(os.getcwd(), "instance", "app.db")}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'setup-key',
        'TESTING': True,
        'ENABLE_ANALYTICS': False  # Disable analytics during setup
    })
    db.init_app(app)
    return app

def remove_database():
    """Remove existing database file and instance directory if they exist."""
    try:
        # Remove instance directory completely to ensure clean state
        instance_dir = os.path.join(os.getcwd(), 'instance')
        if os.path.exists(instance_dir):
            logger.info("Removing instance directory...")
            shutil.rmtree(instance_dir)
            logger.info("Instance directory removed successfully")
        
        # Create fresh instance directory
        os.makedirs(instance_dir, exist_ok=True)
        logger.info(f"Created instance directory: {instance_dir}")
        
        # Create cache directory
        cache_dir = os.path.join(instance_dir, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Created cache directory: {cache_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error removing database: {e}")
        return False

def init_database(app):
    """Initialize database and create tables."""
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            
            # Import all necessary models
            from app.models.user import User
            from app.models.role import Role
            from app.models.permission import Permission
            from app.models.activity import UserActivity, PageVisit
            from app.models.navigation import NavigationCategory, PageRouteMapping
            from app.models.metrics import MetricAlert
            from app.models.permissions import Action, RoutePermission, permission_actions, role_permissions
            from app.models.analytics import (
                FeatureUsage, DocumentAnalytics, ProjectMetrics,
                TeamProductivity, ResourceUtilization
            )
            
            # Create all tables
            db.create_all()
            
            # Initialize default actions
            logger.info("Initializing default actions...")
            default_actions = [
                ('read', 'GET', 'Read access'),
                ('write', 'POST', 'Create access'),
                ('update', 'PUT', 'Update access'),
                ('delete', 'DELETE', 'Delete access'),
                ('list', 'GET', 'List access'),
            ]
            
            actions = {}  # Store actions by name for easy lookup
            for name, method, description in default_actions:
                action = Action.query.filter_by(name=name, method=method).first()
                if not action:
                    action = Action(
                        name=name,
                        method=method,
                        description=description,
                        created_by='system'
                    )
                    db.session.add(action)
                actions[name] = action
            
            db.session.commit()
            logger.info("Default actions initialized successfully")
            
            # Initialize permissions
            logger.info("Initializing permissions...")
            Permission.initialize_default_permissions()
            logger.info("Default permissions initialized successfully")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {', '.join(tables)}")
            
            # Verify specific tables exist
            required_tables = [
                'user', 'role', 'permission', 'action',
                'feature_usage', 'resource_utilization',
                'user_activity', 'page_visit',
                'page_route_mapping',
                'permission_actions', 'role_permissions'  # Association tables
            ]
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                raise Exception(f"Missing required tables: {', '.join(missing_tables)}")
            
            # Verify permissions were created
            permissions = Permission.query.all()
            logger.info("Created permissions:")
            for p in permissions:
                logger.info(f"- {p.name} (actions: {', '.join(a.name for a in p.actions)})")
            
            # Verify each permission has its required actions
            for name, details in ADMIN_PERMISSIONS.items():
                permission = Permission.query.filter_by(name=name).first()
                if not permission:
                    raise Exception(f"Permission {name} not found")
                
                permission_actions = [a.name for a in permission.actions]
                missing_actions = [a for a in details['actions'] if a not in permission_actions]
                if missing_actions:
                    raise Exception(f"Permission {name} missing actions: {', '.join(missing_actions)}")
            
            logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def init_roles(app):
    """Initialize role templates."""
    try:
        with app.app_context():
            logger.info("Initializing role templates...")
            from app.utils.role_templates import initialize_default_roles
            success = initialize_default_roles()
            if success:
                # Get Administrator role and ensure it has all admin permissions
                from app.models import Role, Permission
                admin_role = Role.query.filter_by(name='Administrator').first()
                if admin_role:
                    # Get all admin permissions
                    admin_permissions = Permission.query.filter(
                        Permission.name.like('admin_%')
                    ).all()
                    
                    if not admin_permissions:
                        logger.error("No admin permissions found")
                        return False
                    
                    # Clear existing permissions and assign all admin permissions
                    admin_role.permissions = admin_permissions
                    db.session.commit()
                    
                    # Verify permissions were assigned
                    admin_role = Role.query.filter_by(name='Administrator').first()
                    assigned_permissions = [p.name for p in admin_role.permissions]
                    logger.info(f"Administrator role has permissions: {', '.join(assigned_permissions)}")
                    
                    # Verify each required permission is assigned
                    missing_permissions = []
                    for name in ADMIN_PERMISSIONS.keys():
                        if name not in assigned_permissions:
                            missing_permissions.append(name)
                    
                    if missing_permissions:
                        logger.error(f"Missing required permissions: {', '.join(missing_permissions)}")
                        return False
                    
                    logger.info("Role templates initialized successfully")
                    return True
                else:
                    logger.error("Administrator role not found")
                    return False
            else:
                logger.error("Failed to initialize role templates")
                return False
    except Exception as e:
        logger.error(f"Error initializing roles: {e}")
        return False

def setup_admin(app):
    """Set up admin user."""
    try:
        with app.app_context():
            logger.info("Setting up admin user...")
            
            # Import models
            from app.models.user import User
            from app.models.role import Role
            
            # Create admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                logger.info("Creating admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    name='System Administrator',
                    is_active=True
                )
                admin_user.set_password('admin')
                db.session.add(admin_user)
                db.session.flush()  # Get the user ID
            else:
                admin_user.set_password('admin')
            
            # Get Administrator role
            admin_role = Role.query.filter_by(name='Administrator').first()
            if not admin_role:
                logger.error("Administrator role not found")
                return False
            
            # Clear existing roles and assign Administrator role
            admin_user.roles = []  # Clear existing roles
            admin_user.roles.append(admin_role)
            
            db.session.commit()
            
            # Verify role assignment
            admin_user = User.query.filter_by(username='admin').first()
            if admin_role not in admin_user.roles:
                logger.error("Failed to assign Administrator role to admin user")
                return False
            
            # Log user and role details
            logger.info("Admin user setup completed successfully")
            logger.info("\nAdmin User Details:")
            logger.info(f"Username: {admin_user.username}")
            logger.info(f"Email: {admin_user.email}")
            logger.info("Password: admin")
            logger.info(f"Roles: {', '.join(role.name for role in admin_user.roles)}")
            logger.info(f"Permissions: {', '.join(p.name for r in admin_user.roles for p in r.permissions)}")
            
            # Verify user has required permissions and actions
            for name, details in ADMIN_PERMISSIONS.items():
                permission = next((p for p in admin_user.roles[0].permissions if p.name == name), None)
                if not permission:
                    logger.error(f"Admin user missing permission: {name}")
                    return False
                
                permission_actions = [a.name for a in permission.actions]
                missing_actions = [a for a in details['actions'] if a not in permission_actions]
                if missing_actions:
                    logger.error(f"Permission {name} missing actions: {', '.join(missing_actions)}")
                    return False
            
            return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting up admin user: {e}")
        return False

def main():
    """Main setup function."""
    # Create app instance
    app = create_app()

    steps = [
        ("Removing existing database", remove_database),
        ("Initializing database", lambda: init_database(app)),
        ("Initializing roles", lambda: init_roles(app)),
        ("Setting up admin user", lambda: setup_admin(app)),
        ("Starting application", lambda: app.run(host='0.0.0.0', port=5000, debug=True))
    ]

    for step_name, step_func in steps:
        logger.info(f"\n=== {step_name} ===")
        success = step_func()
        if not success:
            logger.error(f"Setup failed at step: {step_name}")
            sys.exit(1)

if __name__ == '__main__':
    main()
