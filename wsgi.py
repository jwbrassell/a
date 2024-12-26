#!/usr/bin/env python3
"""WSGI entry point for the Flask application."""
import os
import logging
import sys
from app import create_app
from config_migrate import MigrateConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the Flask application
if len(sys.argv) > 1 and sys.argv[1] == 'db':
    # Use MigrateConfig for database migrations
    app = create_app(MigrateConfig)
else:
    # Use normal config for running the app
    from config import config
    env = os.getenv('FLASK_ENV', 'production')
    config_class = config[env]
    # Ensure Vault is initialized for database_reports
    if hasattr(config_class, 'SKIP_VAULT_INIT'):
        config_class.SKIP_VAULT_INIT = False
    app = create_app(config_class)

if __name__ == '__main__':
    app.run()
