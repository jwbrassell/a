#!/usr/bin/env python3
"""Assign admin permissions to Administrator role."""

from app import create_app, db
from app.models import Role, Permission
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def assign_admin_permissions():
    """Assign all admin permissions to Administrator role."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get Administrator role
            admin_role = Role.query.filter_by(name='Administrator').first()
            if not admin_role:
                logger.error("Administrator role not found")
                return False
            
            # Get all admin permissions
            admin_permissions = Permission.query.filter(
                Permission.name.like('admin_%')
            ).all()
            
            # Assign permissions to role
            for permission in admin_permissions:
                if permission not in admin_role.permissions:
                    admin_role.permissions.append(permission)
                    logger.info(f"Added permission: {permission.name}")
            
            db.session.commit()
            logger.info("Successfully assigned admin permissions to Administrator role")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning permissions: {e}")
            return False

if __name__ == '__main__':
    success = assign_admin_permissions()
    if not success:
        logger.error("Failed to assign admin permissions")
        exit(1)
