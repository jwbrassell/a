#!/usr/bin/env python3
"""
Script to migrate existing RBAC data to the enhanced RBAC system.
This script should be run after applying the database migrations.
"""
import os
import sys
from flask import current_app
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Role, User
from app.models.permissions import Permission, Action, RoutePermission
from app.utils.enhanced_rbac import init_default_actions, migrate_existing_mappings, setup_role_hierarchy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_role_hierarchy():
    """Verify role hierarchy is properly set up."""
    try:
        roles = Role.query.all()
        hierarchy_issues = []
        
        for role in roles:
            if role.parent:
                logger.info(f"Role {role.name} has parent {role.parent.name}")
                # Verify no circular dependencies
                current = role.parent
                visited = {role.id}
                while current:
                    if current.id in visited:
                        hierarchy_issues.append(f"Circular dependency detected for role {role.name}")
                        break
                    visited.add(current.id)
                    current = current.parent
        
        return len(hierarchy_issues) == 0, hierarchy_issues
    except Exception as e:
        logger.error(f"Error verifying role hierarchy: {str(e)}")
        return False, [str(e)]

def verify_permissions():
    """Verify permissions are properly set up."""
    try:
        permissions = Permission.query.all()
        permission_issues = []
        
        for permission in permissions:
            # Verify permission has at least one action
            if not permission.actions:
                permission_issues.append(f"Permission {permission.name} has no actions")
            
            # Verify permission is assigned to at least one role
            if not permission.roles:
                permission_issues.append(f"Permission {permission.name} is not assigned to any roles")
            
            # Verify route permissions exist
            route_perms = RoutePermission.query.filter_by(permission_id=permission.id).all()
            if not route_perms:
                permission_issues.append(f"Permission {permission.name} has no route mappings")
        
        return len(permission_issues) == 0, permission_issues
    except Exception as e:
        logger.error(f"Error verifying permissions: {str(e)}")
        return False, [str(e)]

def verify_actions():
    """Verify actions are properly set up."""
    try:
        actions = Action.query.all()
        action_issues = []
        
        expected_actions = {
            ('read', 'GET'),
            ('write', 'POST'),
            ('update', 'PUT'),
            ('delete', 'DELETE'),
            ('list', 'GET')
        }
        
        actual_actions = {(action.name, action.method) for action in actions}
        
        missing_actions = expected_actions - actual_actions
        if missing_actions:
            action_issues.append(f"Missing actions: {missing_actions}")
        
        return len(action_issues) == 0, action_issues
    except Exception as e:
        logger.error(f"Error verifying actions: {str(e)}")
        return False, [str(e)]

def run_migration():
    """Run the migration to enhanced RBAC system."""
    try:
        app = create_app()
        with app.app_context():
            logger.info("Starting migration to enhanced RBAC system...")
            
            # Step 1: Initialize default actions
            logger.info("Initializing default actions...")
            init_default_actions()
            
            # Step 2: Migrate existing mappings
            logger.info("Migrating existing route mappings...")
            if not migrate_existing_mappings():
                raise Exception("Failed to migrate existing mappings")
            
            # Step 3: Set up role hierarchy
            logger.info("Setting up role hierarchy...")
            hierarchy = {
                'user': 'manager',
                'manager': 'admin'
            }
            if not setup_role_hierarchy(hierarchy):
                raise Exception("Failed to set up role hierarchy")
            
            # Step 4: Verify migration
            logger.info("Verifying migration...")
            
            # Verify role hierarchy
            hierarchy_success, hierarchy_issues = verify_role_hierarchy()
            if not hierarchy_success:
                logger.error("Role hierarchy verification failed:")
                for issue in hierarchy_issues:
                    logger.error(f"  - {issue}")
            
            # Verify permissions
            permissions_success, permission_issues = verify_permissions()
            if not permissions_success:
                logger.error("Permissions verification failed:")
                for issue in permission_issues:
                    logger.error(f"  - {issue}")
            
            # Verify actions
            actions_success, action_issues = verify_actions()
            if not actions_success:
                logger.error("Actions verification failed:")
                for issue in action_issues:
                    logger.error(f"  - {issue}")
            
            if hierarchy_success and permissions_success and actions_success:
                logger.info("Migration completed successfully!")
                return True
            else:
                logger.error("Migration completed with issues")
                return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

def rollback_migration():
    """Rollback the enhanced RBAC migration."""
    try:
        app = create_app()
        with app.app_context():
            logger.info("Rolling back enhanced RBAC migration...")
            
            # Remove role hierarchy
            Role.query.update({Role.parent_id: None})
            
            # Remove permissions and related data
            RoutePermission.query.delete()
            Permission.query.delete()
            Action.query.delete()
            
            db.session.commit()
            logger.info("Rollback completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate to enhanced RBAC system')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)
