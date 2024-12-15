"""
Main setup orchestration module
"""
import os
import sys
import importlib
from pathlib import Path
from dotenv import load_dotenv

from utils.setup.args import parse_args
from utils.setup.config import SetupConfig, DatabaseSetup, EnvironmentSetup
from utils.setup.core_setup import CoreDataSetup
from utils.setup.vault_setup import setup_vault
from utils.setup.post_setup import run_post_setup

def init_database(app, config: SetupConfig):
    """Initialize database and core data"""
    from app import db, create_app
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models.documents import Document, Category, Tag, DocumentHistory
    from app.models.analytics import SystemMetric, ApplicationMetric, UserMetric, FeatureUsage, ResourceMetric
    from app.models.user import User
    from app.models.role import Role
    from app.models.permission import Permission
    from app.models.metrics import SystemMetric, ApplicationMetric, UserMetric
    from app.models.activity import Activity
    from app.models.navigation import NavigationItem
    
    with app.app_context():
        try:
            # First create all tables
            db.create_all()
            print("\nCreated database tables")
            
            # Initialize core data
            CoreDataSetup.init_core_data()
            CoreDataSetup.init_navigation()
            db.session.commit()
            print("Core data initialization complete")
            
            # Initialize plugin data if not skipped
            if not config.skip_plugins:
                # Import here to avoid circular dependencies
                from utils.setup.plugin_setup import PluginManager
                PluginManager.init_all_plugins()
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
    
    # Skip migrations initially but allow plugin loading for model registration
    os.environ['SKIP_MIGRATIONS'] = '1'
    
    # Create app with plugins to ensure all models are registered
    from app import create_app
    app = create_app(skip_session=True)
    
    # Initialize database and core data
    if not init_database(app, config):
        print("\nSetup failed during database initialization")
        sys.exit(1)
    
    # Set up Vault (non-blocking)
    setup_vault(config)
    
    print("\nInitial setup complete!")
    
    # Run post-setup initialization
    try:
        run_post_setup()
    except Exception as e:
        print(f"\nWarning: Post-setup initialization failed: {e}")
        print("You can run post_setup.py separately to complete initialization")
    
    print("\nYou can now start the application with:")
    print("Development:")
    print("  flask run")
    print("\nProduction:")
    print("  gunicorn -c gunicorn.conf.py wsgi:app")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: admin")

if __name__ == "__main__":
    setup()
