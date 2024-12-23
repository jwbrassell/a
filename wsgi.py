#!/usr/bin/env python3
"""WSGI entry point for the Flask application."""
import os
import subprocess
import time
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_vault_running():
    """Ensure Vault is running and initialized."""
    try:
        # Load Vault credentials first
        if os.path.exists('.env.vault'):
            with open('.env.vault', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Check if Vault is running
        response = subprocess.run(['vault', 'status'], capture_output=True)
        if response.returncode in [0, 1, 2]:  # 0=running, 1=uninitialized, 2=sealed
            logger.info("Vault is running")
            return True
            
        logger.info("Starting Vault...")
        subprocess.run(['./start_vault.sh'], check=True)
        return True
        
    except Exception as e:
        logger.error(f"Error checking Vault status: {e}")
        return False

# Load environment variables from .env.vault if it exists
if os.path.exists('.env.vault'):
    with open('.env.vault', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Check Vault status but don't fail if it's already running
ensure_vault_running()

# Create the Flask application
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    app.run()
