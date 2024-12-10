import os
import warnings
import logging
import hvac
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from /etc/vault.env
def load_env_file(file_path):
    try:
        load_dotenv(file_path)
        logger.info(f"Loaded environment variables from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load environment variables from {file_path}: {e}")
        raise

# Suppress specific deprecation warning
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="The raise_on_deleted_version parameter will change its default value to False in hvac v3.8.8."
)

class VaultUtility:
    def __init__(self, vault_url=None, token=None, env_file_path='/etc/vault.env'):
        """
        Initialize VaultUtility with URL and token, loading from environment if not provided.
        
        Args:
            vault_url (str, optional): Vault server URL
            token (str, optional): Vault authentication token
            env_file_path (str): Path to environment file
        """
        # Initialize Vault URL
        self.vault_url = vault_url or os.getenv("VAULT_URL", "http://127.0.0.1:8200")
        
        # Initialize token
        self.token = token or os.getenv("VAULT_TOKEN")
        if not self.token:
            try:
                load_env_file(env_file_path)
                self.token = os.getenv("VAULT_TOKEN")
            except Exception as e:
                logger.error(f"Failed to load token from environment: {e}")
                
        if not self.token:
            logger.error("VAULT_TOKEN not found in environment variables")
            raise ValueError("VAULT_TOKEN environment variable not set")

        # Initialize Vault client
        try:
            self.client = self.authenticate_vault(self.vault_url, self.token)
            self.kv_v2_mount_point = self.get_kv_v2_mount_point()
            logger.info("Successfully initialized Vault client")
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise

    def authenticate_vault(self, vault_url, token):
        """
        Authenticate with Vault and return the client.
        
        Args:
            vault_url (str): Vault server URL
            token (str): Vault authentication token
            
        Returns:
            hvac.Client: Authenticated Vault client
        """
        try:
            client = hvac.Client(url=vault_url, token=token)
            if not client.is_authenticated():
                raise ValueError("Vault authentication failed")
            logger.info("Successfully authenticated with Vault")
            return client
        except Exception as e:
            logger.error(f"Vault authentication failed: {e}")
            raise

    def list_keys_recursively(self, path=""):
        """
        List all keys recursively for the kv-v2 engine.
        
        Args:
            path (str): Path to list keys from
            
        Returns:
            list: List of keys
        """
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                mount_point=self.kv_v2_mount_point,
                path=path
            )
            return response['data']['keys']
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Invalid path: {path}")
            return []
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise

    def get_kv_v2_mount_point(self):
        """
        Get the mount point for the kv-v2 secrets engine.
        
        Returns:
            str: Mount point path
        """
        try:
            mounts = self.client.sys.list_mounted_secrets_engines()
            for mount_point, details in mounts.items():
                if details.get('type') == 'kv' and details.get('options', {}).get('version') == '2':
                    logger.info(f"Found kv-v2 mount point: {mount_point}")
                    return mount_point.rstrip('/')
            raise ValueError("No kv-v2 secrets engine found")
        except Exception as e:
            logger.error(f"Failed to get kv-v2 mount points: {e}")
            raise

    def get_value_for_key(self, key):
        """
        Get value for a specified key in the kv-v2 engine.
        
        Args:
            key (str): Key to retrieve value for
            
        Returns:
            Any: Value stored at key
        """
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.kv_v2_mount_point,
                path=key,
                raise_on_deleted_version=True
            )
            return secret['data']['data']
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Key not found: {key}")
            return None
        except Exception as e:
            logger.error(f"Failed to get value for key {key}: {e}")
            return None