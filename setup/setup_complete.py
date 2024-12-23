#!/usr/bin/env python3
"""
Comprehensive setup script that:
1. Initializes all blueprint permissions
2. Creates admin account with full permissions
3. Ensures all blueprints are properly registered
"""
import os
import sys
import logging
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.utils.enhanced_rbac import register_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_blueprint_permissions():
    """Initialize permissions for all blueprints."""
    try:
        logger.info("Initializing blueprint permissions...")
        
        # AWS Manager permissions
        aws_permissions = [
            ('aws_access', 'Access AWS manager', 'aws'),
            ('aws_create_config', 'Create AWS configurations', 'aws'),
            ('aws_delete_config', 'Delete AWS configurations', 'aws'),
            ('aws_manage_ec2', 'Manage EC2 instances', 'aws'),
            ('aws_manage_iam', 'Manage IAM users', 'aws'),
            ('aws_manage_security', 'Manage security groups', 'aws'),
            ('aws_manage_templates', 'Manage EC2 templates', 'aws')
        ]

        # Database Reports permissions
        db_permissions = [
            ('db_reports_access', 'Access database reports', 'database'),
            ('db_reports_create', 'Create new reports', 'database'),
            ('db_reports_edit', 'Edit existing reports', 'database'),
            ('db_reports_delete', 'Delete reports', 'database'),
            ('db_reports_execute', 'Execute reports', 'database')
        ]

        # OnCall permissions
        oncall_permissions = [
            ('oncall_access', 'Access oncall system', 'oncall'),
            ('oncall_manage', 'Manage oncall schedules', 'oncall'),
            ('oncall_view', 'View oncall schedules', 'oncall')
        ]

        # Projects permissions
        project_permissions = [
            ('project_access', 'Access projects', 'projects'),
            ('project_create', 'Create projects', 'projects'),
            ('project_edit', 'Edit projects', 'projects'),
            ('project_delete', 'Delete projects', 'projects')
        ]

        # Core app permissions
        core_permissions = [
            ('admin_access', 'Access admin panel', 'admin'),
            ('user_manage', 'Manage users', 'admin'),
            ('role_manage', 'Manage roles', 'admin'),
            ('permission_manage', 'Manage permissions', 'admin')
        ]

        # Register all permissions
        all_permissions = (
            aws_permissions + 
            db_permissions + 
            oncall_permissions + 
            project_permissions + 
            core_permissions
        )

        for name, description, category in all_permissions:
            register_permission(
                name=name,
                description=description,
                category=category
            )

        logger.info("Blueprint permissions initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize blueprint permissions: {e}")
        return False

def create_admin_role():
    """Create admin role with all permissions."""
    try:
        logger.info("Creating admin role...")
        
        # Create or get admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator role with full access',
                weight=100,
                created_by='system',
                is_system_role=True
            )
            db.session.add(admin_role)
        
        # Add all permissions to admin role
        all_permissions = Permission.query.all()
        admin_role.permissions = all_permissions
        
        db.session.commit()
        logger.info("Admin role created successfully")
        return admin_role
    except Exception as e:
        logger.error(f"Failed to create admin role: {e}")
        db.session.rollback()
        return None

def create_admin_user(admin_role):
    """Create admin user with admin role."""
    try:
        logger.info("Creating admin user...")
        
        # Create or update admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                name='Administrator',
                email='admin@example.com'
            )
            admin_user.set_password('admin')  # Default password
            db.session.add(admin_user)
        
        # Ensure admin user has admin role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
        
        db.session.commit()
        logger.info("Admin user created successfully")
        return admin_user
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.session.rollback()
        return None

def verify_setup():
    """Verify the complete setup."""
    try:
        logger.info("Verifying setup...")
        
        # Check admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            logger.error("Admin user not found")
            return False
        
        # Check admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            logger.error("Admin role not found")
            return False
        
        # Check permissions
        permissions = Permission.query.all()
        if not permissions:
            logger.error("No permissions found")
            return False
        
        # Verify admin has all permissions
        admin_permissions = admin_user.get_permissions()
        if len(admin_permissions) != len(permissions):
            logger.error("Admin user doesn't have all permissions")
            return False
        
        logger.info("Setup verification completed successfully")
        return True
    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        return False

def main():
    """Main setup function."""
    try:
        # Create Flask app context
        app = create_app()
        with app.app_context():
            # Initialize permissions
            if not init_blueprint_permissions():
                raise Exception("Failed to initialize permissions")
            
            # Create admin role
            admin_role = create_admin_role()
            if not admin_role:
                raise Exception("Failed to create admin role")
            
            # Create admin user
            admin_user = create_admin_user(admin_role)
            if not admin_user:
                raise Exception("Failed to create admin user")
            
            # Verify setup
            if not verify_setup():
                raise Exception("Setup verification failed")
        
        logger.info("""
Application setup completed successfully!

The following has been configured:
1. Blueprint permissions
2. Admin role with all permissions
3. Admin user account

You can now log in with:
Username: admin
Password: admin

Please change the admin password after first login.
""")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
