#!/usr/bin/env python3
"""
Complete application setup script that handles:
1. Directory setup
2. Vault configuration and startup
3. Database initialization
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create and configure required directories."""
    directories = [
        'instance',
        'instance/cache',
        'logs',
        'vault-data',
        'vault-audit',
        'vault-plugins',
        'vault-backup',
        'vault-logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        os.chmod(directory, 0o755)
        logger.info(f"Created directory: {directory}")

    # Create uploads directory for documents
    uploads_dir = os.path.join('app', 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    os.chmod(uploads_dir, 0o755)
    logger.info(f"Created directory: {uploads_dir}")

def setup_vault():
    """Configure and start Vault server."""
    try:
        # Start Vault server with development configuration
        logger.info("Starting Vault server...")
        vault_config = 'config/vault-dev.hcl'
        
        # Set environment variables for Vault
        os.environ['VAULT_ADDR'] = 'http://127.0.0.1:8200'
        
        # Check if Vault is already running
        try:
            subprocess.run(['vault', 'status'], check=True, capture_output=True)
            logger.info("Vault is already running")
            return None
        except subprocess.CalledProcessError:
            pass
        
        # Start Vault server
        vault_process = subprocess.Popen(['vault', 'server', '-config=' + vault_config],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        
        # Wait for Vault to start
        time.sleep(5)
        
        # Initialize Vault if needed
        logger.info("Initializing Vault...")
        init_result = subprocess.run(['vault', 'operator', 'init',
                                    '-key-shares=1',
                                    '-key-threshold=1',
                                    '-format=json'],
                                   capture_output=True, text=True)
        
        if init_result.returncode == 0:
            logger.info("Vault initialized successfully")
            # Save init output to a secure file
            init_data = json.loads(init_result.stdout)
            with open('instance/vault-init.json', 'w') as f:
                json.dump(init_data, f, indent=2)
            os.chmod('instance/vault-init.json', 0o600)
            
            # Unseal Vault using the key
            unseal_key = init_data['unseal_keys_b64'][0]
            subprocess.run(['vault', 'operator', 'unseal', unseal_key], check=True)
            
            # Set root token in environment
            os.environ['VAULT_TOKEN'] = init_data['root_token']
            
            # Update .env.vault file
            with open('.env.vault', 'w') as f:
                f.write(f"""# Vault Development Configuration
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN={init_data['root_token']}
VAULT_SKIP_VERIFY=true
""")
            os.chmod('.env.vault', 0o600)
            
        else:
            logger.warning("Vault may already be initialized")
        
        return vault_process
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set up Vault: {e}")
        raise

def init_database():
    """Initialize the database."""
    try:
        logger.info("Initializing database...")
        # Set environment variables to skip Vault and plugin loading during init
        env = os.environ.copy()
        env['SKIP_PLUGIN_LOAD'] = '1'
        env['SKIP_VAULT'] = '1'
        env['FLASK_ENV'] = 'development'
        env['FLASK_APP'] = 'wsgi.py'
        
        # Create SQLite database directory
        db_dir = os.path.join(os.getcwd(), 'instance')
        os.makedirs(db_dir, exist_ok=True)
        os.chmod(db_dir, 0o755)
        
        # Set database path
        db_path = os.path.join(db_dir, 'app.db')
        env['SQLITE_PATH'] = db_path
        
        # Initialize database
        subprocess.run([sys.executable, 'init_db.py'], 
                      env=env,
                      check=True)
        logger.info("Database initialized successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def main():
    """Main setup function."""
    try:
        # Set up directories
        setup_directories()
        
        # Initialize database first
        init_database()
        
        # Set up and start Vault
        vault_process = setup_vault()
        
        logger.info("""
Application setup completed successfully!

The following components have been configured:
1. Directory structure
2. Database (initialized)
3. Vault server (running)

Vault credentials have been saved to:
- instance/vault-init.json
- .env.vault

To start using the application:
1. Start the Flask development server:
   flask run

Remember to:
- Keep the Vault unseal keys and root token secure
- Monitor the logs in the logs directory
- Regularly backup the database and Vault data
""")
        
        # Keep Vault running if we started it
        if vault_process:
            vault_process.wait()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
