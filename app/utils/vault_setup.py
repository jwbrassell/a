#!/usr/bin/env python3
"""
Integrated Vault Setup Script
This script checks if Vault is running and sets it up if needed.
"""

import os
import sys
import subprocess
import logging
import json
import time
import shutil
import platform
import requests
import zipfile
from pathlib import Path

# Import from root directory
from vault_utility import VaultUtility, VaultError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedVaultSetup:
    def __init__(self):
        # Use current working directory instead of hardcoded path
        self.app_root = Path(os.getcwd())
        self.vault_data_dir = self.app_root / "vault-data"
        self.bin_dir = self.app_root / "bin"
        self.config_dir = self.app_root / "config"
        self.vault_binary = self.bin_dir / ("vault.exe" if sys.platform == "win32" else "vault")
        self.env_file = self.app_root / ".env"
        self.vault_env_file = self.app_root / ".env.vault"
        
        # Vault installation settings
        self.vault_version = "1.13.3"  # Latest stable version
        self.os_type = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # Map architecture names
        arch_map = {
            'x86_64': 'amd64',
            'aarch64': 'arm64',
            'arm64': 'arm64'
        }
        self.arch = arch_map.get(self.arch, self.arch)

    def is_vault_running(self):
        """Check if Vault is running and accessible."""
        try:
            # Try to initialize VaultUtility
            vault_util = VaultUtility(env_file_path=str(self.vault_env_file))
            return vault_util.client.is_authenticated()
        except Exception:
            return False

    def get_download_url(self):
        """Get the appropriate Vault download URL for the current system."""
        if self.os_type == "darwin":
            os_name = "darwin"
        elif self.os_type == "linux":
            os_name = "linux"
        elif self.os_type == "windows":
            os_name = "windows"
        else:
            raise Exception(f"Unsupported operating system: {self.os_type}")

        url = f"https://releases.hashicorp.com/vault/{self.vault_version}/vault_{self.vault_version}_{os_name}_{self.arch}.zip"
        return url

    def install_vault(self):
        """Download and install Vault."""
        try:
            url = self.get_download_url()
            logger.info(f"Downloading Vault from: {url}")
            
            # Download Vault
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            zip_path = self.app_root / "vault.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract Vault
            self.bin_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(zip_path) as zip_ref:
                zip_ref.extractall(self.bin_dir)
            
            # Make vault executable
            if not sys.platform == "win32":
                os.chmod(self.vault_binary, 0o755)
            
            # Clean up zip file
            zip_path.unlink()
            
            # Verify installation
            result = subprocess.run(
                [str(self.vault_binary), 'version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Vault installation verified: {result.stdout.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install Vault: {e}")
            return False

    def ensure_vault_installed(self):
        """Ensure Vault is installed."""
        if not self.vault_binary.exists():
            logger.info("Vault not found. Installing...")
            if not self.install_vault():
                raise Exception("Failed to install Vault")
        return True

    def kill_existing_vault(self):
        """Kill any existing Vault processes."""
        try:
            if sys.platform == "win32":
                subprocess.run(['taskkill', '/F', '/IM', 'vault.exe'], capture_output=True)
            else:
                subprocess.run(['pkill', 'vault'], capture_output=True)
            time.sleep(2)
        except Exception:
            pass

    def wait_for_vault(self, env, max_attempts=30):
        """Wait for Vault to be ready"""
        logger.info("Waiting for Vault to start...")
        for i in range(max_attempts):
            try:
                result = subprocess.run(
                    [str(self.vault_binary), 'status', '-format=json'],
                    capture_output=True,
                    text=True,
                    env=env
                )
                if result.returncode in [0, 2]:  # 0 = unsealed, 2 = sealed
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def update_env_file(self, token):
        """Update .env file with Vault token"""
        if self.env_file.exists():
            content = self.env_file.read_text()
            
            # Remove existing Vault settings
            lines = [line for line in content.splitlines() 
                    if not line.startswith(('VAULT_TOKEN=', 'VAULT_ADDR=', 'VAULT_SKIP_VERIFY='))]
            
            # Add new Vault settings
            lines.extend([
                '',
                '# Vault Configuration',
                'VAULT_ADDR=http://127.0.0.1:8201',
                f'VAULT_TOKEN={token}',
                'VAULT_SKIP_VERIFY=true'
            ])
            
            # Write updated content
            self.env_file.write_text('\n'.join(lines))
            logger.info("Updated .env file with Vault configuration")

    def setup_kvv2_engine(self, env):
        """Setup KVv2 secrets engine"""
        try:
            result = subprocess.run(
                [str(self.vault_binary), 'secrets', 'list', '-format=json'],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                mounts = json.loads(result.stdout)
                if 'kvv2/' not in mounts:
                    subprocess.run([
                        str(self.vault_binary),
                        'secrets',
                        'enable',
                        '-path=kvv2',
                        '-version=2',
                        'kv'
                    ], check=True, env=env)
                    logger.info("Mounted KVv2 secrets engine at kvv2/")
                else:
                    logger.info("KVv2 secrets engine already mounted at kvv2/")
        except Exception as e:
            logger.error(f"Failed to setup KVv2 engine: {e}")
            raise

    def initialize_vault(self):
        """Initialize and start Vault server."""
        try:
            # Kill any existing Vault process
            self.kill_existing_vault()
            
            # Setup environment
            env = os.environ.copy()
            env["PATH"] = str(self.bin_dir) + os.pathsep + env["PATH"]
            env["VAULT_ADDR"] = "http://127.0.0.1:8201"
            
            # Start the Vault server
            logger.info("Starting Vault server...")
            server_process = subprocess.Popen([
                str(self.vault_binary),
                'server',
                '-config=' + str(self.config_dir / 'vault-dev.hcl')
            ], env=env)

            # Wait for Vault to be ready
            if not self.wait_for_vault(env):
                raise Exception("Vault failed to start")

            # Initialize Vault with single key share
            logger.info("Initializing new Vault instance...")
            init_result = subprocess.run(
                [
                    str(self.vault_binary),
                    'operator',
                    'init',
                    '-key-shares=1',
                    '-key-threshold=1',
                    '-format=json'
                ],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )

            init_data = json.loads(init_result.stdout)
            root_token = init_data['root_token']
            unseal_key = init_data['unseal_keys_b64'][0]

            # Save root token and unseal key
            self.vault_env_file.write_text(
                f"VAULT_TOKEN={root_token}\n"
                f"VAULT_UNSEAL_KEY={unseal_key}\n"
            )

            # Update .env file with Vault token
            self.update_env_file(root_token)

            # Unseal Vault
            logger.info("Unsealing Vault...")
            subprocess.run([
                str(self.vault_binary),
                'operator',
                'unseal',
                unseal_key
            ], check=True, env=env)

            # Set token in environment
            env['VAULT_TOKEN'] = root_token

            # Verify Vault status
            status_result = subprocess.run(
                [str(self.vault_binary), 'status', '-format=json'],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            status = json.loads(status_result.stdout)
            if status.get('sealed', True):
                raise Exception("Vault is still sealed after unseal operation")

            # Setup KVv2 engine
            self.setup_kvv2_engine(env)

            # Verify we can authenticate
            try:
                vault_util = VaultUtility(env_file_path=str(self.vault_env_file))
                if not vault_util.client.is_authenticated():
                    raise Exception("Failed to authenticate with new token")
            except Exception as e:
                raise Exception(f"Failed to verify Vault authentication: {e}")

            logger.info("Vault initialized and unsealed successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vault: {e}")
            raise

    def setup(self):
        """Run the complete setup process."""
        try:
            logger.info("Checking Vault status...")
            
            if self.is_vault_running():
                logger.info("Vault is already running and accessible.")
                return True
                
            logger.info("Vault is not running. Starting setup process...")
            
            # Ensure Vault is installed
            self.ensure_vault_installed()
            
            # Clean up existing data if needed
            if self.vault_data_dir.exists():
                shutil.rmtree(self.vault_data_dir)
            self.vault_data_dir.mkdir(exist_ok=True)
            
            # Initialize Vault
            self.initialize_vault()

            # Final verification
            if not self.is_vault_running():
                raise Exception("Vault setup completed but service is not accessible")

            logger.info("Vault setup completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Vault setup failed: {e}")
            return False

def setup_vault():
    """Main function to setup Vault."""
    setup = IntegratedVaultSetup()
    return setup.setup()

if __name__ == "__main__":
    setup_vault()
