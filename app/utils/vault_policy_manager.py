import logging
from typing import Dict, List, Optional
from vault_utility import VaultUtility, VaultError

logger = logging.getLogger(__name__)

class VaultPolicyManager:
    """Manages Vault policies and their integration with Flask RBAC."""
    
    def __init__(self, vault_utility: Optional[VaultUtility] = None):
        self.vault = vault_utility or VaultUtility()
        
    def create_blueprint_policy(self, blueprint_name: str, paths: List[Dict[str, str]]) -> bool:
        """
        Create a Vault policy for a specific blueprint.
        
        Args:
            blueprint_name: Name of the Flask blueprint
            paths: List of path configurations, e.g.:
                  [
                      {
                          "path": "kvv2/data/app1/*",
                          "capabilities": ["read", "list"]
                      }
                  ]
        """
        try:
            policy_name = f"blueprint_{blueprint_name}"
            policy_rules = {
                "path": {
                    path_config["path"]: {
                        "capabilities": path_config["capabilities"]
                    } for path_config in paths
                }
            }
            
            # Add default deny
            policy_rules["path"]["*"] = {"capabilities": ["deny"]}
            
            self.vault.client.sys.create_or_update_policy(
                name=policy_name,
                policy=policy_rules
            )
            
            logger.info(f"Created/updated policy {policy_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create blueprint policy: {e}")
            raise VaultError(f"Policy creation failed: {str(e)}")

    def create_role_policy(self, role_name: str, paths: List[Dict[str, str]]) -> bool:
        """
        Create a Vault policy for a specific role.
        
        Args:
            role_name: Name of the role in Flask
            paths: List of path configurations
        """
        try:
            policy_name = f"role_{role_name}"
            policy_rules = {
                "path": {
                    path_config["path"]: {
                        "capabilities": path_config["capabilities"]
                    } for path_config in paths
                }
            }
            
            self.vault.client.sys.create_or_update_policy(
                name=policy_name,
                policy=policy_rules
            )
            
            logger.info(f"Created/updated policy {policy_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create role policy: {e}")
            raise VaultError(f"Policy creation failed: {str(e)}")

    def setup_ldap_auth(self, ldap_config: Dict) -> bool:
        """
        Configure LDAP authentication in Vault.
        
        Args:
            ldap_config: LDAP configuration dictionary containing:
                        - url: LDAP server URL
                        - binddn: Admin bind DN
                        - bindpass: Admin bind password
                        - userdn: Base DN for user search
                        - groupdn: Base DN for group search
        """
        try:
            # Enable LDAP auth if not already enabled
            if 'ldap/' not in self.vault.client.sys.list_auth_methods():
                self.vault.client.sys.enable_auth_method(
                    method_type='ldap',
                    path='ldap'
                )
            
            # Configure LDAP auth
            self.vault.client.auth.ldap.configure(
                url=ldap_config['url'],
                binddn=ldap_config['binddn'],
                bindpass=ldap_config['bindpass'],
                userdn=ldap_config['userdn'],
                groupdn=ldap_config['groupdn'],
                groupattr="memberOf",
                insecure_tls=False
            )
            
            logger.info("LDAP authentication configured successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup LDAP authentication: {e}")
            raise VaultError(f"LDAP setup failed: {str(e)}")

    def map_ldap_group_to_policies(self, group_name: str, policies: List[str]) -> bool:
        """
        Map an LDAP group to Vault policies.
        
        Args:
            group_name: LDAP group name
            policies: List of policy names to map to the group
        """
        try:
            self.vault.client.auth.ldap.create_or_update_group(
                name=group_name,
                policies=policies
            )
            
            logger.info(f"Mapped group {group_name} to policies: {policies}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to map LDAP group to policies: {e}")
            raise VaultError(f"Group mapping failed: {str(e)}")

    def create_default_policies(self):
        """Create default policies for common use cases."""
        try:
            # Admin policy with full access
            self.create_role_policy("admin", [
                {"path": "kvv2/*", "capabilities": ["create", "read", "update", "delete", "list"]},
                {"path": "sys/policies/*", "capabilities": ["create", "read", "update", "delete", "list"]},
                {"path": "sys/metrics", "capabilities": ["read"]}
            ])
            
            # Read-only policy
            self.create_role_policy("readonly", [
                {"path": "kvv2/data/*", "capabilities": ["read", "list"]}
            ])
            
            # Service account policy
            self.create_role_policy("service", [
                {"path": "kvv2/data/services/*", "capabilities": ["read"]}
            ])

            # Metrics viewer policy
            self.create_role_policy("metrics_viewer", [
                {"path": "sys/metrics", "capabilities": ["read"]}
            ])
            
            logger.info("Created default policies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create default policies: {e}")
            raise VaultError(f"Default policy creation failed: {str(e)}")

    def get_policy_info(self, policy_name: str) -> Dict:
        """Get information about a specific policy."""
        try:
            policy = self.vault.client.sys.read_policy(name=policy_name)
            return {
                "name": policy_name,
                "rules": policy["rules"]
            }
        except Exception as e:
            logger.error(f"Failed to get policy info: {e}")
            raise VaultError(f"Policy info retrieval failed: {str(e)}")

    def list_policies(self) -> List[str]:
        """List all policies."""
        try:
            return self.vault.client.sys.list_policies()["policies"]
        except Exception as e:
            logger.error(f"Failed to list policies: {e}")
            raise VaultError(f"Policy listing failed: {str(e)}")

    def delete_policy(self, policy_name: str) -> bool:
        """Delete a policy."""
        try:
            self.vault.client.sys.delete_policy(name=policy_name)
            logger.info(f"Deleted policy {policy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            raise VaultError(f"Policy deletion failed: {str(e)}")
