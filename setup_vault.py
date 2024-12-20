#!/usr/bin/env python3
"""Script to start and configure Vault server."""
import os
import sys
import json
import logging
import subprocess
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_vault():
    """Start Vault server."""
    try:
        # Check if Vault is already running
        try:
            subprocess.run(['vault', 'status'], check=True, capture_output=True)
            logger.info("Vault is already running")
            return True
        except subprocess.CalledProcessError:
            pass

        # Start Vault server
        logger.info("Starting Vault server...")
        vault_config = 'config/vault-dev.hcl'
        
        # Create log directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Start Vault in background using nohup
        with open('logs/vault.log', 'w') as log_file:
            subprocess.run(['nohup', 'vault', 'server', '-config=' + vault_config, '&'],
                         stdout=log_file,
                         stderr=log_file,
                         start_new_session=True)
        
        # Wait for Vault to start
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                subprocess.run(['vault', 'status'], check=True, capture_output=True)
                logger.info("Vault started successfully")
                return True
            except subprocess.CalledProcessError:
                attempt += 1
                time.sleep(1)
                
        logger.error("Failed to start Vault after multiple attempts")
        return False
            
    except Exception as e:
        logger.error(f"Failed to start Vault: {e}")
        return False

def initialize_vault():
    """Initialize Vault if needed."""
    try:
        # Check if Vault needs initialization
        status = subprocess.run(['vault', 'status'], capture_output=True)
        if status.returncode == 0:
            logger.info("Vault is already initialized")
            return True
            
        # Initialize Vault
        logger.info("Initializing Vault...")
        init_result = subprocess.run(['vault', 'operator', 'init',
                                    '-key-shares=1',
                                    '-key-threshold=1',
                                    '-format=json'],
                                   capture_output=True, text=True)
        
        if init_result.returncode == 0:
            # Save init data
            init_data = json.loads(init_result.stdout)
            os.makedirs('instance', exist_ok=True)
            with open('instance/vault-init.json', 'w') as f:
                json.dump(init_data, f, indent=2)
            os.chmod('instance/vault-init.json', 0o600)
            
            # Unseal Vault
            unseal_key = init_data['unseal_keys_b64'][0]
            subprocess.run(['vault', 'operator', 'unseal', unseal_key], check=True)
            
            # Update .env.vault file
            with open('.env.vault', 'w') as f:
                f.write(f"""VAULT_TOKEN={init_data['root_token']}
VAULT_UNSEAL_KEY={unseal_key}""")
            os.chmod('.env.vault', 0o600)
            
            logger.info("Vault initialized successfully")
            return True
        else:
            logger.error("Failed to initialize Vault")
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize Vault: {e}")
        return False

def main():
    """Main function."""
    try:
        if not start_vault():
            raise Exception("Failed to start Vault")
            
        if not initialize_vault():
            raise Exception("Failed to initialize Vault")
            
        logger.info("""
Vault setup completed successfully!

The following has been configured:
1. Vault server started
2. Vault initialized and unsealed
3. Credentials saved to:
   - instance/vault-init.json
   - .env.vault

You can now proceed with the rest of the application setup.
""")
        
    except Exception as e:
        logger.error(f"Vault setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
