from app.utils.vault_policy_manager import VaultPolicyManager
import logging

logger = logging.getLogger(__name__)

def initialize_vault_policies():
    """Initialize default Vault policies"""
    try:
        policy_manager = VaultPolicyManager()

        # Role-based policies
        policy_manager.create_role_policy('Administrator', [
            {'path': 'kvv2/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'database_creds/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'sys/policies/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'sys/auth/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'sys/mounts/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'sys/health', 'capabilities': ['read']},
            {'path': 'sys/metrics', 'capabilities': ['read']}
        ])
        
        policy_manager.create_role_policy('Manager', [
            {'path': 'kvv2/data/projects/*', 'capabilities': ['create', 'read', 'update', 'list']},
            {'path': 'kvv2/data/documents/*', 'capabilities': ['create', 'read', 'update', 'list']},
            {'path': 'database_creds/*', 'capabilities': ['read', 'list']}
        ])
        
        policy_manager.create_role_policy('User', [
            {'path': 'kvv2/data/projects/*', 'capabilities': ['read', 'list']},
            {'path': 'kvv2/data/documents/*', 'capabilities': ['read', 'list']},
            {'path': 'database_creds/*', 'capabilities': ['read']}
        ])
        
        policy_manager.create_role_policy('metrics_viewer', [
            {'path': 'kvv2/data/metrics/*', 'capabilities': ['read', 'list']}
        ])

        # Blueprint-specific policies
        policy_manager.create_blueprint_policy('documents', [
            {'path': 'kvv2/data/documents/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']}
        ])
        
        policy_manager.create_blueprint_policy('profile', [
            {'path': 'kvv2/data/profiles/*', 'capabilities': ['read', 'update']}
        ])
        
        policy_manager.create_blueprint_policy('admin', [
            {'path': 'kvv2/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']},
            {'path': 'database_creds/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']}
        ])

        # Database reports policies
        policy_manager.create_blueprint_policy('database_reports', [
            {'path': 'database_creds/*', 'capabilities': ['create', 'read', 'update', 'delete', 'list']}
        ])

        # Try to setup LDAP group mappings
        try:
            policy_manager.map_ldap_group_to_policies('admin_group', [
                'role_Administrator',
                'blueprint_admin',
                'blueprint_database_reports'
            ])
            policy_manager.map_ldap_group_to_policies('manager_group', [
                'role_Manager',
                'blueprint_documents',
                'blueprint_database_reports'
            ])
            policy_manager.map_ldap_group_to_policies('user_group', [
                'role_User',
                'blueprint_profile'
            ])
        except Exception as e:
            logger.warning(f"Failed to setup LDAP group mappings: {str(e)}")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Vault policies: {str(e)}")
        return False
