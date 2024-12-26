from config import Config
import sys
import os

class MigrateConfig(Config):
    SKIP_VAULT_INIT = True
    SKIP_DB_INIT = True  # Skip database initialization
    SKIP_BLUEPRINTS = True  # Skip blueprint initialization
    
    # Use null session type for migrations
    SESSION_TYPE = 'null'
    
    # Set SQLite database path
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        # Create instance directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Skip initializations
        app.config['SKIP_VAULT_INIT'] = True
        app.config['SKIP_VAULT_MIDDLEWARE'] = True
        app.config['SKIP_DB_INIT'] = True
        app.config['SKIP_BLUEPRINTS'] = True
