#!/usr/bin/env python3
"""
Development Vault Setup Script
This script sets up a development Vault server with SSL certificates
"""

import os
import sys
import subprocess
import logging
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

    def initialize_vault(self):
        """Initialize and start Vault server."""
        try:
            # Start Vault server
            logger.info("Starting Vault server...")
            env = os.environ.copy()
            env["PATH"] = str(self.bin_dir) + os.pathsep + env["PATH"]
            
            subprocess.Popen([
                str(self.vault_binary),
                'server',
                '-config=config/vault-dev.hcl'
            ], env=env)

            # Wait for Vault to start
            import time
            time.sleep(2)

            # Initialize Vault
            result = subprocess.run([
                str(self.vault_binary),
                'operator', 'init',
                '-key-shares=1',
                '-key-threshold=1',
                '-format=json'
            ], capture_output=True, text=True, check=True, env=env)

            import json
            init_data = json.loads(result.stdout)

            # Save root token and unseal key
            with open('.env.vault', 'w') as f:
                f.write(f"VAULT_TOKEN={init_data['root_token']}\n")
                f.write(f"VAULT_UNSEAL_KEY={init_data['unseal_keys_b64'][0]}\n")

            # Unseal Vault
            subprocess.run([
                str(self.vault_binary),
                'operator', 'unseal',
                init_data['unseal_keys_b64'][0]
            ], check=True, env=env)

            # Enable KV v2 secrets engine
            os.environ['VAULT_TOKEN'] = init_data['root_token']
            subprocess.run([
                str(self.vault_binary),
                'secrets', 'enable',
                '-version=2', 'kv'
            ], check=True, env=env)

            logger.info("Vault initialized successfully!")
            logger.info("\nImportant: Save these credentials securely!")
            logger.info(f"Root Token: {init_data['root_token']}")
            logger.info(f"Unseal Key: {init_data['unseal_keys_b64'][0]}")
            logger.info("\nThese credentials have been saved to .env.vault")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize Vault: {e}")
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

To use the development Vault:
1. Set these environment variables:
   export VAULT_ADDR=https://127.0.0.1:8200
   export VAULT_TOKEN=<token from .env.vault>
   export PATH="%s:$PATH"

2. Update your .env file with:
   VAULT_ADDR=https://127.0.0.1:8200
   VAULT_TOKEN=<token from .env.vault>

3. To verify Vault is running:
   ./bin/vault status

Note: This is a development setup and should not be used in production.
""" % self.bin_dir)

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = VaultDevSetup()
    setup.setup()
