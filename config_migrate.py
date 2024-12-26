from config import Config
import sys
import os

class MigrateConfig(Config):
    SKIP_VAULT_INIT = True
    SKIP_DB_INIT = True  # Skip database initialization
    SKIP_BLUEPRINTS = True  # Skip blueprint initialization
    
    # Set SQLite database path
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        # Create instance directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Skip all blueprint imports
        for module in [
            'app.blueprints.database_reports',
            'app.blueprints.database_reports.connections',
            'app.blueprints.database_reports.models',
            'app.blueprints.projects',
            'app.blueprints.bug_reports',
            'app.blueprints.feature_requests',
            'app.blueprints.weblinks',
            'app.blueprints.example',
            'app.routes.admin',
            'app.routes.profile',
            'app.utils.add_dispatch_routes',
            'app.utils.add_handoff_routes',
            'app.utils.add_oncall_routes',
            'app.utils.add_database_report_routes',
            'app.utils.add_example_routes',
            'app.utils.add_bug_report_routes',
            'app.utils.add_feature_request_routes'
        ]:
            sys.modules[module] = None
        
        # Skip initializations
        app.config['SKIP_VAULT_INIT'] = True
        app.config['SKIP_VAULT_MIDDLEWARE'] = True
        app.config['SKIP_DB_INIT'] = True
        app.config['SKIP_BLUEPRINTS'] = True
