#!/usr/bin/env python3
"""
Development Vault Setup Script
This script sets up a development Vault server with SSL certificates
"""

import os
import sys
import subprocess
import logging
import re
import time
from pathlib import Path
from utils.generate_dev_certs import CertificateGenerator
from utils.install_vault import VaultInstaller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultDevSetup:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.vault_data_dir = self.base_dir / "vault-data"
        self.bin_dir = self.base_dir / "bin"
        self.cert_generator = CertificateGenerator()
        self.vault_binary = self.bin_dir / "vault"
        if sys.platform == "win32":
            self.vault_binary = self.bin_dir / "vault.exe"
        
    def ensure_vault_installed(self):
        """Ensure Vault is installed."""
        if not self.vault_binary.exists():
            logger.info("Vault not found. Installing...")
            installer = VaultInstaller()
            installer.install()
        return True

    def setup_directories(self):
        """Create necessary directories."""
        self.vault_data_dir.mkdir(exist_ok=True)
        logger.info(f"Created Vault data directory: {self.vault_data_dir}")

    def generate_certificates(self):
        """Generate SSL certificates."""
        self.cert_generator.generate()

    def wait_for_vault(self, env, max_attempts=30):
        """Wait for Vault to be ready"""
        logger.info("Waiting for Vault to start...")
        for i in range(max_attempts):
            try:
                result = subprocess.run(
                    [str(self.vault_binary), 'status', '-format=json', '-tls-skip-verify'],
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

    def check_vault_status(self, env):
        """Check if Vault is initialized and sealed"""
        try:
            result = subprocess.run(
                [str(self.vault_binary), 'status', '-format=json', '-tls-skip-verify'],
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode in [0, 2]:  # 0 = unsealed, 2 = sealed
                import json
                status = json.loads(result.stdout)
                return status.get('initialized', False), status.get('sealed', True)
            return False, True
        except Exception as e:
            logger.debug(f"Error checking Vault status: {e}")
            return False, True

    def update_env_file(self, token):
        """Update .env file with Vault token"""
        env_path = Path('.env')
        if env_path.exists():
            content = env_path.read_text()
            
            # Remove existing Vault settings
            lines = [line for line in content.splitlines() 
                    if not line.startswith(('VAULT_TOKEN=', 'VAULT_ADDR=', 'VAULT_SKIP_VERIFY='))]
            
            # Add new Vault settings
            lines.extend([
                '',
                '# Vault Configuration',
                'VAULT_ADDR=https://127.0.0.1:8200',
                f'VAULT_TOKEN={token}',
                'VAULT_SKIP_VERIFY=true'
            ])
            
            # Write updated content
            env_path.write_text('\n'.join(lines))
            logger.info("Updated .env file with Vault configuration")

    def setup_kvv2_engine(self, env):
        """Setup KVv2 secrets engine"""
        try:
            # Check if kvv2 is already mounted
            result = subprocess.run(
                [str(self.vault_binary), 'secrets', 'list', '-format=json', '-tls-skip-verify'],
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                import json
                mounts = json.loads(result.stdout)
                if 'kvv2/' not in mounts:
                    # Mount KVv2 at kvv2/
                    subprocess.run([
                        str(self.vault_binary),
                        'secrets',
                        'enable',
                        '-tls-skip-verify',
                        '-path=kvv2',
                        '-version=2',
                        'kv'
                    ], check=True, env=env)
                    logger.info("Mounted KVv2 secrets engine at kvv2/")
                else:
                    logger.info("KVv2 secrets engine already mounted at kvv2/")
        except subprocess.CalledProcessError as e:
            if "path is already in use" in (e.stderr or ""):
                logger.info("KVv2 secrets engine is already mounted")
            else:
                logger.error(f"Failed to setup KVv2 engine: {e}")
                if e.stderr:
                    logger.error(f"Error output: {e.stderr}")
                raise

    def initialize_vault(self):
        """Initialize and start Vault server."""
        try:
            # Setup environment
            env = os.environ.copy()
            env["PATH"] = str(self.bin_dir) + os.pathsep + env["PATH"]
            env["VAULT_ADDR"] = "https://127.0.0.1:8200"
            env["VAULT_SKIP_VERIFY"] = "true"
            
            # Start the Vault server
            logger.info("Starting Vault server...")
            server_process = subprocess.Popen([
                str(self.vault_binary),
                'server',
                '-config=config/vault-dev.hcl'
            ], env=env)

            # Wait for Vault to be ready
            if not self.wait_for_vault(env):
                raise Exception("Vault failed to start")

            # Check if Vault is already initialized
            initialized, sealed = self.check_vault_status(env)
            
            if initialized:
                logger.info("Vault is already initialized")
                env_vault_path = Path('.env.vault')
                if env_vault_path.exists():
                    env_content = env_vault_path.read_text()
                    token_match = re.search(r'VAULT_TOKEN=(.+)', env_content)
                    
                    if sealed:
                        logger.info("Vault is sealed. Attempting to unseal...")
                        unseal_key_match = re.search(r'VAULT_UNSEAL_KEY=(.+)', env_content)
                        if unseal_key_match:
                            unseal_key = unseal_key_match.group(1).strip()
                            subprocess.run([
                                str(self.vault_binary),
                                'operator',
                                'unseal',
                                '-tls-skip-verify',
                                unseal_key
                            ], check=True, env=env)
                            logger.info("Successfully unsealed Vault")
                    
                    if token_match:
                        token = token_match.group(1).strip()
                        env["VAULT_TOKEN"] = token
                        self.update_env_file(token)
                        self.setup_kvv2_engine(env)
                return

            # Initialize Vault
            logger.info("Initializing new Vault instance...")
            init_cmd = [
                str(self.vault_binary),
                'operator',
                'init',
                '-key-shares=1',
                '-key-threshold=1',
                '-format=json',
                '-tls-skip-verify'
            ]
            
            result = subprocess.run(
                init_cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )

            import json
            init_data = json.loads(result.stdout)

            # Save root token and unseal key
            with open('.env.vault', 'w') as f:
                f.write(f"VAULT_TOKEN={init_data['root_token']}\n")
                f.write(f"VAULT_UNSEAL_KEY={init_data['unseal_keys_b64'][0]}\n")

            # Update .env file with Vault token
            self.update_env_file(init_data['root_token'])

            # Unseal Vault
            unseal_cmd = [
                str(self.vault_binary),
                'operator',
                'unseal',
                '-tls-skip-verify',
                init_data['unseal_keys_b64'][0]
            ]
            subprocess.run(unseal_cmd, check=True, env=env)

            # Set token in environment and setup KVv2
            env['VAULT_TOKEN'] = init_data['root_token']
            self.setup_kvv2_engine(env)

            logger.info("Vault initialized successfully!")
            logger.info("\nImportant: Save these credentials securely!")
            logger.info(f"Root Token: {init_data['root_token']}")
            logger.info(f"Unseal Key: {init_data['unseal_keys_b64'][0]}")
            logger.info("\nThese credentials have been saved to .env.vault")
            logger.info("Vault configuration has been added to .env")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize Vault: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def setup(self):
        """Run the complete setup process."""
        try:
            logger.info("Starting development Vault setup...")
            
            # Ensure Vault is installed
            self.ensure_vault_installed()
            
            self.setup_directories()
            self.generate_certificates()
            self.initialize_vault()

            logger.info("""
Development Vault setup complete!

Vault has been configured with:
1. KVv2 secrets engine mounted at 'kvv2/'
2. Configuration added to .env file
3. Credentials saved in .env.vault

To verify Vault is running:
   ./bin/vault status -tls-skip-verify

Note: This is a development setup and should not be used in production.
""")

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            if hasattr(e, 'stderr'):
                logger.error(f"Error output: {e.stderr}")
            sys.exit(1)

if __name__ == "__main__":
    setup = VaultDevSetup()
    setup.setup()
