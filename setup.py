#!/usr/bin/env python3
"""
Setup script for initializing the application.

This script provides a modular setup process with options to:
1. Choose database type (SQLite/MariaDB)
2. Initialize core data and navigation
3. Initialize plugin data
4. Set up Vault integration
5. Configure environment settings

Usage:
    python setup.py                  # Full setup with SQLite in dev mode
    python setup.py --mariadb       # Use MariaDB instead of SQLite
    python setup.py --env prod      # Production environment setup
    python setup.py --skip-vault    # Skip Vault setup
    python setup.py --skip-plugins  # Skip plugin initialization
"""

import os
import sys
import argparse
import importlib
from pathlib import Path
from dotenv import load_dotenv

# Import setup utilities
from utils.setup_utils import (
    SetupConfig,
    DatabaseSetup,
    EnvironmentSetup,
    CoreDataSetup,
    PluginDataSetup
)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Setup the application with various configuration options.'
    )
    parser.add_argument(
        '--mariadb',
        action='store_true',
        help='Use MariaDB instead of SQLite'
    )
    parser.add_argument(
        '--env',
        choices=['dev', 'prod'],
        default='dev',
        help='Environment to configure (dev or prod)'
    )
    parser.add_argument(
        '--skip-vault',
        action='store_true',
        help='Skip Vault setup'
    )
    parser.add_argument(
        '--skip-plugins',
        action='store_true',
        help='Skip plugin initialization'
    )
    return parser.parse_args()

def setup_vault(config: SetupConfig):
    """Set up Vault if not skipped"""
    if not config.skip_vault:
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

def init_database(app, config: SetupConfig):
    """Initialize database and core data"""
    from app import db
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("\nCreated database tables")
            
            # Initialize core data first
            CoreDataSetup.init_core_data()
            CoreDataSetup.init_navigation()
            db.session.commit()
            print("Core data initialization complete")
            
            # Initialize plugin data if not skipped
            if not config.skip_plugins:
                PluginDataSetup.init_all_plugin_data()
                db.session.commit()
                print("Plugin data initialization complete")
            
            return True
        except Exception as e:
            print(f"\nError during database initialization: {e}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"Caused by: {e.__cause__}")
            return False

def setup():
    """Run the complete setup process"""
    print("Starting application setup...")
    
    # Parse command line arguments
    args = parse_args()
    
    # Create setup configuration
    config = SetupConfig(
        use_mariadb=args.mariadb,
        skip_vault=args.skip_vault,
        skip_plugins=args.skip_plugins,
        env=args.env
    )
    
    # Ensure .env file exists with defaults
    EnvironmentSetup.create_env_file(config)
    
    # Load environment variables
    load_dotenv()
    
    # Reload config module to pick up new environment variables
    import config as app_config
    importlib.reload(app_config)
    
    # Initialize database based on configuration
    if config.use_mariadb:
        os.environ['DB_TYPE'] = 'mariadb'
        print("\nInitializing MariaDB...")
        if not DatabaseSetup.init_mariadb():
            print("\nFailed to initialize MariaDB. Please check the requirements and try again.")
            sys.exit(1)
    else:
        os.environ['DB_TYPE'] = 'sqlite'
        DatabaseSetup.init_sqlite(config.base_dir)
    
    # Skip both migrations and plugins initially
    os.environ['SKIP_MIGRATIONS'] = '1'
    os.environ['SKIP_PLUGIN_LOAD'] = '1'
    
    # Create app without plugins first
    from app import create_app
    app = create_app(skip_session=True)
    
    # Initialize database and core data
    if not init_database(app, config):
        print("\nSetup failed during database initialization")
        sys.exit(1)
    
    # Set up Vault (non-blocking)
    setup_vault(config)
    
    print("\nSetup complete!")
    print("\nYou can now start the application with:")
    print("Development:")
    print("  flask run")
    print("\nProduction:")
    print("  gunicorn -c gunicorn.conf.py wsgi:app")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: test123")

if __name__ == "__main__":
    setup()
