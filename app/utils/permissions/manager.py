"""Permissions manager to handle all module permissions."""
import logging
from typing import List, Tuple, Dict
from app.models.permission import Permission
from app.models.permissions import Action
from app.extensions import db

# Import all module permissions
from .admin import ADMIN_PERMISSIONS
from .aws import AWS_PERMISSIONS
from .handoffs import HANDOFF_PERMISSIONS
from .dispatch import DISPATCH_PERMISSIONS
from .database_reports import DATABASE_REPORTS_PERMISSIONS
from .documents import DOCUMENT_PERMISSIONS
from .oncall import ONCALL_PERMISSIONS

logger = logging.getLogger(__name__)

class PermissionsManager:
    """Manage application permissions across all modules."""
    
    @staticmethod
    def get_all_permissions() -> List[Tuple[str, str]]:
        """Get all permissions from all modules."""
        return (
            ADMIN_PERMISSIONS +
            AWS_PERMISSIONS +
            HANDOFF_PERMISSIONS +
            DISPATCH_PERMISSIONS +
            DATABASE_REPORTS_PERMISSIONS +
            DOCUMENT_PERMISSIONS +
            ONCALL_PERMISSIONS
        )
    
    @staticmethod
    def get_module_permissions(module: str) -> List[Tuple[str, str]]:
        """Get permissions for a specific module."""
        module_map = {
            'admin': ADMIN_PERMISSIONS,
            'aws': AWS_PERMISSIONS,
            'handoffs': HANDOFF_PERMISSIONS,
            'dispatch': DISPATCH_PERMISSIONS,
            'database_reports': DATABASE_REPORTS_PERMISSIONS,
            'documents': DOCUMENT_PERMISSIONS,
            'oncall': ONCALL_PERMISSIONS,
        }
        return module_map.get(module, [])
    
    @staticmethod
    def init_actions() -> List[Action]:
        """Initialize default actions."""
        default_actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access'),
            ('list', 'GET', 'List access'),
        ]
        
        actions = []
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
            actions.append(action)
        db.session.commit()
        return actions
    
    @staticmethod
    def init_permissions() -> None:
        """Initialize all permissions with their actions."""
        # Initialize actions first
        actions = PermissionsManager.init_actions()
        
        # Get all permissions
        all_permissions = PermissionsManager.get_all_permissions()
        
        # Create or update each permission
        for name, description in all_permissions:
            # Check if permission exists
            perm = Permission.query.filter_by(name=name).first()
            if not perm:
                perm = Permission(
                    name=name,
                    description=description,
                    category=name.split('_')[0],
                    created_by='system'
                )
                db.session.add(perm)
                db.session.flush()
            
            # Add all actions to the permission
            for action in actions:
                if action not in perm.actions:
                    perm.actions.append(action)
        
        db.session.commit()
        logger.info(f"Initialized {len(all_permissions)} permissions with {len(actions)} actions")
    
    @staticmethod
    def audit_permissions() -> Dict[str, List[str]]:
        """Audit all permissions and their usage."""
        audit_results = {
            'unused_permissions': [],
            'missing_actions': [],
            'duplicate_permissions': [],
            'inconsistent_naming': [],
        }
        
        # Check for unused permissions
        all_perms = Permission.query.all()
        for perm in all_perms:
            if not perm.roles:
                audit_results['unused_permissions'].append(perm.name)
        
        # Check for permissions missing actions
        for perm in all_perms:
            if not perm.actions:
                audit_results['missing_actions'].append(perm.name)
        
        # Check for duplicate permissions (same name different case)
        perm_names = [p.name.lower() for p in all_perms]
        seen = set()
        for name in perm_names:
            if name in seen:
                audit_results['duplicate_permissions'].append(name)
            seen.add(name)
        
        # Check for inconsistent naming
        for perm in all_perms:
            if not perm.name.islower() or not '_' in perm.name:
                audit_results['inconsistent_naming'].append(perm.name)
        
        return audit_results

    @staticmethod
    def get_permission_usage() -> Dict[str, int]:
        """Get usage statistics for each permission."""
        usage_stats = {}
        all_perms = Permission.query.all()
        
        for perm in all_perms:
            usage_stats[perm.name] = len(perm.roles)
        
        return usage_stats
