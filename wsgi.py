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
        # Check if Vault is running
        status = subprocess.run(['vault', 'status'], capture_output=True)
        if status.returncode in [0]:
            logger.info("Vault is already running and initialized")
            return True
            
        # If not running, start it
        logger.info("Starting Vault...")
        subprocess.run(['./start_vault.sh'], check=True)
        
        # Wait for Vault to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                status = subprocess.run(['vault', 'status'], capture_output=True)
                if status.returncode in [0]:
                    # Load Vault credentials
                    if os.path.exists('.env.vault'):
                        with open('.env.vault', 'r') as f:
                            for line in f:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    os.environ[key] = value
                    logger.info("Vault started successfully")
                    return True
            except:
                pass
            time.sleep(1)
            
        logger.error("Failed to start Vault")
        return False
        
    except Exception as e:
        logger.error(f"Error ensuring Vault is running: {e}")
        return False

# Load environment variables from .env.vault if it exists
if os.path.exists('.env.vault'):
    with open('.env.vault', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Ensure Vault is running before creating the app
if not ensure_vault_running():
    raise RuntimeError("Failed to start Vault")

# Create the Flask application
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    app.run()
