from functools import wraps
from flask import current_app, request, g, abort
from flask_login import current_user
import logging
from typing import Optional, List
from vault_utility import VaultUtility, VaultError
import re
import json

logger = logging.getLogger(__name__)

class VaultPolicyEnforcer:
    """Middleware to enforce Vault policies in Flask blueprints."""
    
    def __init__(self, vault_utility: Optional[VaultUtility] = None):
        self.vault = vault_utility or VaultUtility(env_file_path='.env')
    
    def _get_user_policies(self) -> List[str]:
        """Get policies associated with the current user."""
        try:
            if not current_user or not current_user.is_authenticated:
                return []
                
            # Get LDAP groups if using LDAP
            if hasattr(current_user, 'ldap_groups'):
                groups = current_user.ldap_groups
                policies = []
                for group in groups:
                    try:
                        group_policies = self.vault.client.auth.ldap.read_group(
                            name=group
                        )['policies']
                        policies.extend(group_policies)
                    except Exception:
                        continue
                return list(set(policies))
            
            # Fallback to role-based policies
            if hasattr(current_user, 'roles'):
                # Use exact role names for policy lookup
                return [f"role_{role.name}" for role in current_user.roles]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get user policies: {e}")
            return []

    def _path_matches(self, policy_path: str, request_path: str) -> bool:
        """Check if a request path matches a policy path pattern."""
        try:
            # Convert vault policy path pattern to regex pattern
            pattern = policy_path.replace('*', '.*')
            pattern = f"^{pattern}$"
            return bool(re.match(pattern, request_path))
        except Exception as e:
            logger.error(f"Error in path matching: {e}")
            return False

    def _parse_policy_rules(self, policy_str: str) -> dict:
        """Parse policy rules from string format to dictionary."""
        try:
            # If it's already a dict, return it
            if isinstance(policy_str, dict):
                return policy_str
            
            # Try parsing as JSON first
            try:
                return json.loads(policy_str)
            except json.JSONDecodeError:
                pass
            
            # Parse HCL-style policy string
            rules = {}
            current_path = None
            
            for line in policy_str.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Path declaration
                if line.startswith('path'):
                    path = line.split('"')[1]
                    current_path = path
                    rules[current_path] = {}
                
                # Capabilities
                elif line.startswith('capabilities'):
                    caps = [cap.strip(' "[]') for cap in line.split('=')[1].strip().split(',')]
                    if current_path:
                        rules[current_path]['capabilities'] = caps
            
            return {'path': rules}
        except Exception as e:
            logger.error(f"Failed to parse policy rules: {e}")
            return {'path': {}}
    
    def _check_path_permission(self, path: str, capability: str) -> bool:
        """Check if user has permission for the given path and capability."""
        try:
            # Get user's policies
            policies = self._get_user_policies()
            if not policies:
                logger.warning(f"No policies found for user {current_user.get_id()}")
                return False
            
            logger.info(f"Checking policies for user {current_user.get_id()}: {policies}")
            
            # Check each policy
            for policy_name in policies:
                try:
                    policy = self.vault.client.sys.read_policy(name=policy_name)
                    if not policy:
                        logger.warning(f"Policy {policy_name} not found")
                        continue
                    
                    # Parse policy rules
                    policy_rules = self._parse_policy_rules(policy['rules'])
                    
                    # Check each path in the policy
                    for policy_path, rules in policy_rules.get('path', {}).items():
                        # If the policy path matches our request path
                        if self._path_matches(policy_path, path):
                            path_capabilities = rules.get('capabilities', [])
                            if capability in path_capabilities:
                                logger.info(f"Permission granted by policy {policy_name} for path {path} with capability {capability}")
                                return True
                except Exception as e:
                    logger.warning(f"Failed to check policy {policy_name}: {e}")
                    continue
            
            logger.warning(f"No matching policy found for path {path} with capability {capability}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check path permission: {e}")
            return False
    
    def requires_vault_permission(self, path: str, capability: str):
        """
        Decorator to enforce Vault permissions on routes.
        
        Args:
            path: Vault path to check (e.g., "kvv2/data/app1/*")
            capability: Required capability ("read", "write", etc.)
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    if not self._check_path_permission(path, capability):
                        logger.warning(
                            f"Access denied to {path} with capability {capability} "
                            f"for user {current_user.get_id()}"
                        )
                        abort(403)
                    return f(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in vault permission check: {e}")
                    abort(500)
            return decorated_function
        return decorator

def init_vault_middleware(app, vault_utility=None):
    """Initialize Vault middleware for the Flask app."""
    enforcer = VaultPolicyEnforcer(vault_utility)
    
    @app.before_request
    def check_vault_status():
        """Check Vault status before each request."""
        try:
            if not enforcer.vault.client.is_authenticated():
                g.vault_available = False
                g.vault_error = "Vault authentication failed"
            else:
                g.vault_available = True
                g.vault_error = None
        except Exception as e:
            g.vault_available = False
            g.vault_error = str(e)
            logger.error(f"Vault status check failed: {e}")

    # Make enforcer available to the app
    app.vault_policy_enforcer = enforcer
    
    # Add template context processor
    @app.context_processor
    def inject_vault_status():
        return {
            'vault_available': g.get('vault_available', False),
            'vault_error': g.get('vault_error', None)
        }
    
    return enforcer
