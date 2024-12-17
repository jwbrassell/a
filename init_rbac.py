#!/usr/bin/env python3
"""Initialize RBAC system with permissions, actions, and roles."""

from app import create_app, db
from app.models import Role, Permission, Action
from app.utils.enhanced_rbac import init_default_actions
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_rbac():
    """Initialize RBAC system."""
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Initialize default actions
            logger.info("Initializing default actions...")
            init_default_actions()
            
            # 2. Create admin permissions with actions
            logger.info("Creating admin permissions...")
            admin_permissions = [
                ('admin_dashboard_access', 'Access to admin dashboard'),
                ('admin_users_access', 'Access to user management'),
                ('admin_roles_access', 'Access to role management'),
                ('admin_monitoring_access', 'Access to system monitoring'),
                ('admin_logs_access', 'Access to system logs'),
                ('admin_vault_access', 'Access to vault management')
            ]
            
            # Get all actions
            actions = Action.query.all()
            
            for name, description in admin_permissions:
                permission = Permission.query.filter_by(name=name).first()
                if not permission:
                    permission = Permission(
                        name=name,
                        description=description,
                        category='admin',
                        created_by='system'
                    )
                    db.session.add(permission)
                    logger.info(f"Created permission: {name}")
                
                # Add all actions to permission
                for action in actions:
                    if action not in permission.actions:
                        permission.actions.append(action)
            
            db.session.commit()
            
            # 3. Assign permissions to Administrator role
            logger.info("Assigning permissions to Administrator role...")
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
            logger.info("RBAC system initialized successfully")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing RBAC system: {e}")
            return False

if __name__ == '__main__':
    success = init_rbac()
    if not success:
        logger.error("Failed to initialize RBAC system")
        exit(1)
