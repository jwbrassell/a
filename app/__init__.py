from flask import Flask
from config import Config
from app.utils.vault_middleware import init_vault_middleware
from app.utils.vault_defaults import initialize_vault_policies
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Configure app
    if isinstance(config_class, str):
        from config import config
        config_class = config.get(config_class, config['default'])
    app.config.from_object(config_class)
    
    # Initialize config
    config_class.init_app(app)

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)
    
    # Initialize template filters
    from app.template_filters import init_app as init_template_filters
    init_template_filters(app)
    
    # Initialize Vault middleware
    vault_enforcer = init_vault_middleware(app)
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/flask_app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask application startup')

    # Initialize routes
    from app.routes import init_routes
    init_routes(app)

    # Initialize profile module
    from app.routes.profile import init_profile
    init_profile(app)

    # Initialize dispatch routes
    with app.app_context():
        try:
            from app.utils.add_dispatch_routes import add_dispatch_routes
            if add_dispatch_routes():
                app.logger.info("Dispatch routes initialized successfully")
            else:
                app.logger.warning("Failed to initialize dispatch routes")
        except Exception as e:
            app.logger.error(f"Error initializing dispatch routes: {e}")

    # Initialize Vault policies after blueprints are registered
    with app.app_context():
        try:
            if initialize_vault_policies():
                app.logger.info("Vault policies initialized successfully")
            else:
                app.logger.warning("Failed to initialize Vault policies")
        except Exception as e:
            app.logger.error(f"Error initializing Vault policies: {e}")

        # Setup vault during app context
        try:
            from app.utils.vault_setup import setup_vault
            if setup_vault():
                app.logger.info("Vault setup completed successfully")
            else:
                app.logger.warning("Vault setup failed")
        except Exception as e:
            app.logger.error(f"Error during Vault setup: {e}")

    return app
