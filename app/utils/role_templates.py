"""Role template management functionality."""

from app.models import Role, Permission
from app import db
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Define basic role templates
ROLE_TEMPLATES = {
    'administrator': {
        'name': 'Administrator',
        'description': 'Full system access with all administrative privileges',
        'permissions': ['admin_*'],  # Wildcard for all admin permissions
        'icon': 'fa-user-shield',
        'is_system_role': True,
        'weight': 100
    },
    'basic_user': {
        'name': 'Basic User',
        'description': 'Standard user access with basic permissions',
        'permissions': [
            'profile_access',
            'documents_read',
            'analytics_view'
        ],
        'icon': 'fa-user',
        'is_system_role': True,
        'weight': 10
    },
    'read_only': {
        'name': 'Read Only User',
        'description': 'View-only access to system resources',
        'permissions': [
            'documents_read',
            'analytics_view'
        ],
        'icon': 'fa-eye',
        'is_system_role': True,
        'weight': 5
    }
}

def create_role_from_template(template_name: str, custom_name: Optional[str] = None) -> Role:
    """Create a new role from a template."""
    if template_name not in ROLE_TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = ROLE_TEMPLATES[template_name]
    
    try:
        # Create role with template attributes
        role = Role(
            name=custom_name or template['name'],
            description=template['description'],
            icon=template['icon'],
            is_system_role=template['is_system_role'],
            weight=template['weight'],
            created_by='system'  # Add created_by field
        )
        
        # Handle permissions
        permissions = []
        for perm_name in template['permissions']:
            if perm_name.endswith('*'):
                # Handle wildcard permissions
                base_name = perm_name[:-1]
                perms = Permission.query.filter(
                    Permission.name.like(f"{base_name}%")
                ).all()
                permissions.extend(perms)
            else:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm:
                    permissions.append(perm)
        
        role.permissions = permissions
        db.session.add(role)
        db.session.commit()
        
        logger.info(f"Created role from template '{template_name}': {role.name}")
        return role
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating role from template: {e}")
        raise

def initialize_default_roles():
    """Initialize default roles from templates if they don't exist."""
    try:
        for template_name, template in ROLE_TEMPLATES.items():
            # Check if role already exists
            existing_role = Role.query.filter_by(name=template['name']).first()
            if not existing_role:
                create_role_from_template(template_name)
                logger.info(f"Initialized default role: {template['name']}")
            else:
                logger.info(f"Default role already exists: {template['name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing default roles: {e}")
        return False

def list_available_templates() -> List[Dict[str, Any]]:
    """List all available role templates."""
    return [
        {
            'id': name,
            'name': template['name'],
            'description': template['description'],
            'permissions': template['permissions']
        }
        for name, template in ROLE_TEMPLATES.items()
    ]

def get_template_details(template_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific template."""
    if template_name not in ROLE_TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = ROLE_TEMPLATES[template_name]
    return {
        'id': template_name,
        'name': template['name'],
        'description': template['description'],
        'permissions': template['permissions'],
        'icon': template['icon'],
        'is_system_role': template['is_system_role'],
        'weight': template['weight']
    }

def validate_template_permissions(template_name: str) -> List[str]:
    """Validate that all permissions in a template exist."""
    if template_name not in ROLE_TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = ROLE_TEMPLATES[template_name]
    missing_permissions = []
    
    for perm_name in template['permissions']:
        if perm_name.endswith('*'):
            # Skip validation for wildcard permissions
            continue
            
        perm = Permission.query.filter_by(name=perm_name).first()
        if not perm:
            missing_permissions.append(perm_name)
    
    return missing_permissions
