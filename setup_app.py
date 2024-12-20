#!/usr/bin/env python3
"""
Unified setup script for the Flask application with Vault integration.
This script handles:
1. Vault setup and initialization
2. Database initialization
3. Admin account and permissions setup
4. Complete verification
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.utils.permissions import PermissionsManager
from sqlalchemy import inspect, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_vault():
    """Set up Vault using the shell script."""
    try:
        # Make script executable
        os.chmod('start_vault.sh', 0o755)
        
        # Run the script
        result = subprocess.run(['./start_vault.sh'], check=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Vault setup failed: {result.stderr}")
            return False
            
        # Load Vault credentials
        if os.path.exists('.env.vault'):
            with open('.env.vault', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            
        logger.info("Vault setup completed successfully")
        return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Vault setup script: {e}")
        return False
    except Exception as e:
        logger.error(f"Error setting up Vault: {e}")
        return False

def setup_database():
    """Initialize database and create required tables."""
    try:
        app = create_app()
        with app.app_context():
            # Get list of all tables except flask_sessions
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Drop all tables except flask_sessions
            for table in existing_tables:
                if table != 'flask_sessions':
                    db.session.execute(text(f'DROP TABLE IF EXISTS {table}'))
            db.session.commit()
            
            logger.info("Creating database tables...")
            db.create_all()
            
            # Initialize permissions using PermissionsManager
            PermissionsManager.init_permissions()
            
            # Create admin role and user
            create_admin_role_and_user()
            
            # Verify setup within the same context
            if not verify_setup(app):
                raise Exception("Setup verification failed")
            
            logger.info("Database setup completed successfully")
            return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def create_admin_role_and_user():
    """Create admin role and user with full permissions."""
    try:
        # Create admin role
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
            db.session.flush()  # Ensure role is created before adding permissions
        
        # Add all permissions to admin role
        all_permissions = Permission.query.all()
        admin_role.permissions = all_permissions
        
        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                name='Administrator',
                email='admin@example.com'
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)
        
        # Ensure admin user has admin role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
        
        db.session.commit()
        logger.info("Admin role and user created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create admin role and user: {e}")
        db.session.rollback()
        return False

def verify_setup(app=None):
    """Verify the complete setup."""
    try:
        # Check Vault
        status = subprocess.run(['vault', 'status'], capture_output=True)
        if status.returncode not in [0]:
            logger.error("Vault is not properly initialized")
            return False
        
        # Check database and permissions
        if app is None:
            app = create_app()
        
        # Use existing context if available
        if app.app_context():
            ctx = app.app_context()
        else:
            ctx = app.app_context()
            ctx.push()
            
        try:
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
            admin_permissions = [p.name for p in admin_role.permissions]
            if len(admin_permissions) != len(permissions):
                logger.error("Admin user doesn't have all permissions")
                return False
            
            # Verify admin user has admin role
            if not admin_user.has_role('admin'):
                logger.error("Admin user does not have admin role")
                return False
            
            # Verify admin user has all permissions through role
            user_permissions = admin_user.get_permissions()
            if len(user_permissions) != len(permissions):
                logger.error("Admin user does not have all permissions through role")
                return False
            
            # Run permission audit
            audit_results = PermissionsManager.audit_permissions()
            if audit_results['missing_actions'] or audit_results['duplicate_permissions']:
                logger.error("Permission audit failed")
                return False
            
            logger.info("Setup verification completed successfully")
            return True
        finally:
            if not app.app_context():
                ctx.pop()
                
    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        return False

def main():
    """Main setup function."""
    try:
        # Set up Vault
        if not setup_vault():
            raise Exception("Failed to set up Vault")
        
        # Set up database
        if not setup_database():
            raise Exception("Failed to set up database")
        
        logger.info("""
Setup completed successfully!

The following has been configured:
1. Vault server running and initialized
2. Database tables created
3. Permissions and roles configured
4. Admin account created

You can now:
1. Start the Flask application with:
   flask run

2. Log in with:
   Username: admin
   Password: admin

3. Run permission audit with:
   python audit_permissions.py

Remember to:
- Keep your Vault credentials secure (in instance/vault-init.json and .env.vault)
- Change the admin password after first login
- Monitor the logs in the logs directory
""")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
