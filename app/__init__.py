from flask import Flask, request, send_from_directory
from config import Config
from app.utils.vault_middleware import init_vault_middleware
from app.utils.vault_defaults import initialize_vault_policies
from app.utils.init_db import init_database
import logging
from logging.handlers import RotatingFileHandler
import os
import mimetypes

# Import base models at module level
from app.models import *

def create_app(config_class=Config):
    # Import weblinks models
    from app.blueprints.weblinks.models import WebLink, Tag, WebLinkHistory

    # Ensure correct MIME types are set
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('text/css', '.min.css')
    mimetypes.add_type('application/javascript', '.min.js')
    mimetypes.add_type('application/x-font-woff', '.woff')
    mimetypes.add_type('application/x-font-woff2', '.woff2')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/x-font-otf', '.otf')
    mimetypes.add_type('image/svg+xml', '.svg')
    
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

    # Custom static file handler
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith(('.css', '.min.css')):
            response.headers['Content-Type'] = 'text/css; charset=utf-8'
        elif filename.endswith(('.js', '.min.js')):
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
    
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

    # Initialize database
    with app.app_context():
        if init_database():
            app.logger.info("Database initialized successfully")
        else:
            app.logger.error("Failed to initialize database")

    # Initialize projects blueprint first
    with app.app_context():
        try:
            from app.blueprints.projects import init_app as init_projects
            if init_projects(app):
                app.logger.info("Projects blueprint initialized successfully")
            else:
                app.logger.warning("Failed to initialize projects blueprint")
        except Exception as e:
            app.logger.error(f"Error initializing projects blueprint: {e}")

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

    # Initialize handoff routes
    with app.app_context():
        try:
            from app.utils.add_handoff_routes import add_handoff_routes
            if add_handoff_routes():
                app.logger.info("Handoff routes initialized successfully")
            else:
                app.logger.warning("Failed to initialize handoff routes")
        except Exception as e:
            app.logger.error(f"Error initializing handoff routes: {e}")

    # Initialize on-call routes
    with app.app_context():
        try:
            from app.utils.add_oncall_routes import add_oncall_routes
            if add_oncall_routes():
                app.logger.info("On-call routes initialized successfully")
            else:
                app.logger.warning("Failed to initialize on-call routes")
        except Exception as e:
            app.logger.error(f"Error initializing on-call routes: {e}")

    # Initialize weblinks blueprint
    with app.app_context():
        try:
            from app.blueprints.weblinks import init_app as init_weblinks
            if init_weblinks(app):
                app.logger.info("WebLinks blueprint initialized successfully")
            else:
                app.logger.warning("Failed to initialize weblinks blueprint")
        except Exception as e:
            app.logger.error(f"Error initializing weblinks blueprint: {e}")

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
