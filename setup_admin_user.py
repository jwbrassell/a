#!/usr/bin/env python3
"""Set up admin user with appropriate roles and permissions."""

from app import create_app, db
from app.models import User, Role
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_admin_user():
    """Create or update admin user with appropriate roles."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                logger.info("Creating admin user...")
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    name='System Administrator',
                    is_active=True
                )
                admin_user.set_password('admin')  # Use set_password method
                db.session.add(admin_user)
            else:
                # Update password if user exists
                admin_user.set_password('admin')  # Use set_password method
            
            # Get or create Administrator role
            admin_role = Role.query.filter_by(name='Administrator').first()
            if not admin_role:
                logger.error("Administrator role not found. Please run init_role_templates.py first")
                return False
            
            # Assign Administrator role if not already assigned
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
                logger.info("Assigned Administrator role to admin user")
            
            db.session.commit()
            logger.info("Admin user setup completed successfully")
            
            # Show admin user details
            logger.info("\nAdmin User Details:")
            logger.info(f"Username: {admin_user.username}")
            logger.info(f"Email: {admin_user.email}")
            logger.info("Password: admin (please change this)")
            logger.info(f"Roles: {', '.join(role.name for role in admin_user.roles)}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting up admin user: {e}")
            return False

if __name__ == '__main__':
    success = setup_admin_user()
    if not success:
        logger.error("Failed to set up admin user")
        exit(1)
