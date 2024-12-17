"""Default Vault policy configurations for the application."""
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default policies for different roles
DEFAULT_POLICIES = {
    "Administrator": [
        {
            "path": "kvv2/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/policies/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/auth/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/metrics/*",
            "capabilities": ["read"]
        }
    ],
    "Manager": [
        {
            "path": "kvv2/data/team/*",
            "capabilities": ["read", "list"]
        },
        {
            "path": "kvv2/data/projects/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/metrics/*",
            "capabilities": ["read"]
        }
    ],
    "User": [
        {
            "path": "kvv2/data/public/*",
            "capabilities": ["read", "list"]
        },
        {
            "path": "kvv2/data/user/${identity.entity.name}/*",
            "capabilities": ["create", "read", "update", "delete"]
        }
    ],
    "metrics_viewer": [
        {
            "path": "sys/metrics/*",
            "capabilities": ["read"]
        }
    ]
}

# Blueprint-specific policies
BLUEPRINT_POLICIES = {
    "documents": [
        {
            "path": "kvv2/data/documents/*",
            "capabilities": ["read", "list"]
        }
    ],
    "profile": [
        {
            "path": "kvv2/data/user/${identity.entity.name}/*",
            "capabilities": ["read", "update"]
        }
    ],
    "admin": [
        {
            "path": "kvv2/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/policies/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/auth/*",
            "capabilities": ["create", "read", "update", "delete", "list"]
        },
        {
            "path": "sys/metrics/*",
            "capabilities": ["read"]
        }
    ]
}

# LDAP group mappings
LDAP_GROUP_MAPPINGS = {
    "admin_group": ["Administrator_policy", "blueprint_admin"],
    "manager_group": ["Manager_policy", "blueprint_documents"],
    "user_group": ["User_policy", "blueprint_profile"],
    "metrics_group": ["metrics_viewer_policy"]
}

def setup_default_policies(policy_manager):
    """Setup default policies in Vault."""
    try:
        # Create role-based policies
        for role, paths in DEFAULT_POLICIES.items():
            policy_manager.create_role_policy(role, paths)
        
        # Create blueprint-specific policies
        for blueprint, paths in BLUEPRINT_POLICIES.items():
            policy_manager.create_blueprint_policy(blueprint, paths)
        
        # Map LDAP groups to policies if LDAP is configured
        try:
            for group, policies in LDAP_GROUP_MAPPINGS.items():
                policy_manager.map_ldap_group_to_policies(group, policies)
        except Exception as e:
            logger.warning(f"Failed to setup LDAP group mappings: {e}")
            
        return True
    except Exception as e:
        logger.error(f"Failed to initialize vault policies: {e}")
        return False

def initialize_vault_policies():
    """Initialize all vault policies and mappings."""
    try:
        from vault_utility import VaultUtility
        from app.utils.vault_policy_manager import VaultPolicyManager
        
        vault_util = VaultUtility()
        policy_manager = VaultPolicyManager(vault_util)
        
        # Setup default policies
        return setup_default_policies(policy_manager)
        
    except Exception as e:
        logger.error(f"Failed to initialize vault policies: {e}")
        return False
