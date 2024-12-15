"""
Vault initialization and configuration module
"""
import os
from pathlib import Path
from utils.setup.config import SetupConfig

def setup_vault(config: SetupConfig):
    """Set up Vault if not skipped"""
    if config.skip_vault:
        print("\nSkipping Vault setup (--skip-vault flag used)")
        return
    
    try:
        # Set environment variables for Vault
        os.environ['VAULT_SKIP_VERIFY'] = 'true'  # Skip TLS verification for self-signed certs
        os.environ['VAULT_ADDR'] = 'https://127.0.0.1:8200'
        
        from setup_dev_vault import VaultDevSetup
        print("\nInitializing Vault...")
        vault_setup = VaultDevSetup()
        vault_setup.setup()
        
        # Add Vault configuration to .env file
        env_path = Path('.env')
        if env_path.exists():
            content = env_path.read_text()
            if 'VAULT_ADDR' not in content:
                with env_path.open('a') as f:
                    f.write('\n# Vault Configuration\n')
                    f.write('VAULT_ADDR=https://127.0.0.1:8200\n')
                    f.write('VAULT_SKIP_VERIFY=true\n')
                print("Added Vault configuration to .env file")
        
    except Exception as e:
        print(f"\nWarning: Vault setup failed: {e}")
        print("You can run setup_dev_vault.py separately to set up Vault")
        print("Continuing with rest of setup...")
