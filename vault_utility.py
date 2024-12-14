import os
import warnings
import logging
import secrets
import hvac
from functools import wraps
from urllib.parse import urlparse
from dotenv import load_dotenv
from flask import current_app, request, abort
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress specific deprecation warning
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="The raise_on_deleted_version parameter will change its default value to False in hvac v3.8.8."
)

def load_env_file(file_path):
    """Load environment variables from specified file."""
    try:
        load_dotenv(file_path)
        logger.info(f"Loaded environment variables from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load environment variables from {file_path}: {e}")
        raise

class VaultError(Exception):
    """Custom exception for Vault-related errors."""
    pass

class CSRFProtection:
    """CSRF token management using Vault for storage."""
    
    def __init__(self, vault_client, mount_point):
        self.client = vault_client
        self.mount_point = mount_point
        self.csrf_path = "csrf/tokens"
        
    def generate_token(self):
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=24)
        
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.mount_point,
                path=f"{self.csrf_path}/{token}",
                secret=dict(
                    expiry=expiry.isoformat(),
                    created=datetime.utcnow().isoformat()
                )
            )
            return token
        except Exception as e:
            logger.error(f"Failed to store CSRF token: {e}")
            raise VaultError("Failed to generate CSRF token")

    def validate_token(self, token):
        """Validate a CSRF token."""
        try:
            result = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point,
                path=f"{self.csrf_path}/{token}"
            )
            
            data = result["data"]["data"]
            expiry = datetime.fromisoformat(data["expiry"])
            
            if datetime.utcnow() > expiry:
                self.delete_token(token)
                return False
                
            return True
        except hvac.exceptions.InvalidPath:
            return False
        except Exception as e:
            logger.error(f"Failed to validate CSRF token: {e}")
            return False

    def delete_token(self, token):
        """Delete a CSRF token."""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=self.mount_point,
                path=f"{self.csrf_path}/{token}"
            )
        except Exception as e:
            logger.error(f"Failed to delete CSRF token: {e}")

def csrf_protected(f):
    """Decorator for CSRF protection."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            token = request.headers.get("X-CSRF-Token")
            if not token or not current_app.csrf.validate_token(token):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

class PluginCredentialManager:
    """Manage credentials for plugins."""
    
    def __init__(self, vault_client, mount_point):
        self.client = vault_client
        self.mount_point = mount_point
        self.plugins_path = "plugins"

    def store_plugin_credentials(self, plugin_name, credentials):
        """Store credentials for a plugin."""
        try:
            path = f"{self.plugins_path}/{plugin_name}"
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.mount_point,
                path=path,
                secret=credentials
            )
            logger.info(f"Stored credentials for plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to store credentials for plugin {plugin_name}: {e}")
            raise VaultError(f"Failed to store credentials for {plugin_name}")

    def get_plugin_credentials(self, plugin_name):
        """Retrieve credentials for a plugin."""
        try:
            path = f"{self.plugins_path}/{plugin_name}"
            result = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point,
                path=path
            )
            return result["data"]["data"]
        except hvac.exceptions.InvalidPath:
            logger.warning(f"No credentials found for plugin: {plugin_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get credentials for plugin {plugin_name}: {e}")
            raise VaultError(f"Failed to retrieve credentials for {plugin_name}")

    def rotate_plugin_credentials(self, plugin_name, new_credentials):
        """Rotate credentials for a plugin."""
        try:
            old_credentials = self.get_plugin_credentials(plugin_name)
            if old_credentials:
                # Store old credentials in history
                history_path = f"{self.plugins_path}/{plugin_name}/history"
                self.client.secrets.kv.v2.create_or_update_secret(
                    mount_point=self.mount_point,
                    path=history_path,
                    secret={"previous": old_credentials}
                )
            
            # Store new credentials
            self.store_plugin_credentials(plugin_name, new_credentials)
            logger.info(f"Rotated credentials for plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to rotate credentials for plugin {plugin_name}: {e}")
            raise VaultError(f"Failed to rotate credentials for {plugin_name}")

class VaultUtility:
    def __init__(self, vault_url=None, token=None, env_file_path='.env.vault'):
        """Initialize VaultUtility with URL and token."""
        # Load environment if needed
        if not vault_url or not token:
            try:
                load_env_file(env_file_path)
            except Exception as e:
                logger.error(f"Failed to load environment: {e}")
                raise

        # Initialize Vault URL with HTTPS enforcement
        self.vault_url = vault_url or os.getenv("VAULT_ADDR")
        if not self.vault_url:
            raise VaultError("VAULT_ADDR environment variable not set")
        
        # Enforce HTTPS in production
        if not os.getenv("FLASK_ENV") == "development":
            parsed_url = urlparse(self.vault_url)
            if parsed_url.scheme != "https":
                raise VaultError("HTTPS is required for Vault communication in production")
        
        # Validate URL is localhost
        parsed_url = urlparse(self.vault_url)
        if parsed_url.hostname not in ["localhost", "127.0.0.1"]:
            raise VaultError("Vault must be accessed via localhost only")
        
        # Initialize token
        self.token = token or os.getenv("VAULT_TOKEN")
        if not self.token:
            raise VaultError("VAULT_TOKEN environment variable not set")

        # Initialize Vault client
        try:
            self.client = self.authenticate_vault(self.vault_url, self.token)
            self.kv_v2_mount_point = self.get_kv_v2_mount_point()
            
            # Initialize CSRF protection
            self.csrf = CSRFProtection(self.client, self.kv_v2_mount_point)
            
            # Initialize plugin credential manager
            self.plugin_credentials = PluginCredentialManager(
                self.client, 
                self.kv_v2_mount_point
            )
            
            logger.info("Successfully initialized Vault client")
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise

    def authenticate_vault(self, vault_url, token):
        """Authenticate with Vault and return the client."""
        try:
            # Get CA certificate path from environment
            ca_cert = os.getenv("VAULT_CACERT")
            if ca_cert and Path(ca_cert).exists():
                verify = str(Path(ca_cert).resolve())
                logger.info(f"Using CA certificate: {verify}")
            else:
                verify = False
                logger.warning("CA certificate not found or not specified, disabling SSL verification")
            
            client = hvac.Client(
                url=vault_url,
                token=token,
                verify=verify
            )
            
            if not client.is_authenticated():
                raise VaultError("Vault authentication failed")
                
            logger.info("Successfully authenticated with Vault")
            return client
        except Exception as e:
            logger.error(f"Vault authentication failed: {e}")
            raise

    def get_kv_v2_mount_point(self):
        """Get the mount point for the kv-v2 secrets engine."""
        try:
            mounts = self.client.sys.list_mounted_secrets_engines()
            for mount_point, details in mounts.items():
                if details.get('type') == 'kv' and details.get('options', {}).get('version') == '2':
                    logger.info(f"Found kv-v2 mount point: {mount_point}")
                    return mount_point.rstrip('/')
            raise VaultError("No kv-v2 secrets engine found")
        except Exception as e:
            logger.error(f"Failed to get kv-v2 mount points: {e}")
            raise

    def get_secret(self, path):
        """Get a secret from Vault."""
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.kv_v2_mount_point,
                path=path,
                raise_on_deleted_version=True
            )
            return secret["data"]["data"]
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Secret not found: {path}")
            return None
        except Exception as e:
            logger.error(f"Failed to get secret at path {path}: {e}")
            raise VaultError(f"Failed to retrieve secret at {path}")

    def store_secret(self, path, secret):
        """Store a secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.kv_v2_mount_point,
                path=path,
                secret=secret
            )
            logger.info(f"Stored secret at path: {path}")
        except Exception as e:
            logger.error(f"Failed to store secret at path {path}: {e}")
            raise VaultError(f"Failed to store secret at {path}")

    def delete_secret(self, path):
        """Delete a secret from Vault."""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=self.kv_v2_mount_point,
                path=path
            )
            logger.info(f"Deleted secret at path: {path}")
        except Exception as e:
            logger.error(f"Failed to delete secret at path {path}: {e}")
            raise VaultError(f"Failed to delete secret at {path}")

    def list_secrets(self, path=""):
        """List secrets at a path."""
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                mount_point=self.kv_v2_mount_point,
                path=path
            )
            return response["data"]["keys"]
        except hvac.exceptions.InvalidPath:
            logger.warning(f"No secrets found at path: {path}")
            return []
        except Exception as e:
            logger.error(f"Failed to list secrets at path {path}: {e}")
            raise VaultError(f"Failed to list secrets at {path}")
