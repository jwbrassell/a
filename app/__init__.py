from flask import Flask, render_template, redirect, url_for, flash, session
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
from datetime import datetime
import os
import click
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions
from app.extensions import db, login_manager, migrate, cache

# Initialize CSRF protection
csrf = CSRFProtect()

def register_plugins(app):
    """Register plugin blueprints and routes"""
    from app.utils.plugin_manager import PluginManager
    plugin_manager = PluginManager(app)
    
    # Load and register plugin blueprints within app context
    with app.app_context():
        # First register all blueprints
        blueprints = plugin_manager.load_all_plugins()
        for blueprint in blueprints:
            if blueprint:
                app.register_blueprint(blueprint)
        
        # Initialize projects plugin
        from app.plugins.projects import init_app as init_projects
        init_projects(app)
        
        # Initialize dispatch routes
        from app.plugins.dispatch.utils.register_routes import register_dispatch_routes
        register_dispatch_routes()

        # Initialize tracking plugin
        from app.plugins.tracking import init_tracking
        init_tracking(app)

def register_commands(app):
    """Register CLI commands."""
    pass

def create_app(config_name=None, skip_session=False):
    app = Flask(__name__)
    
    # Set configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # Initialize app-specific config

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)  # Initialize CSRF protection
    cache.init_app(app)  # Initialize cache

    # Initialize Flask-Session only if not skipped
    if not skip_session:
        from flask_session import Session
        Session(app)

    # Initialize logging configuration
    from app.logging_utils import init_app as init_logging
    init_logging(app)

    # Skip migrations if requested
    if os.getenv('SKIP_MIGRATIONS') != '1':
        migrate.init_app(app, db)

    # Initialize image registry
    from app.utils.image_registry import ImageRegistry
    ImageRegistry.init_app(app)

    # Configure login
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import and register blueprints
    from app.routes import main as main_bp
    app.register_blueprint(main_bp)

    # Only load plugins if not explicitly skipped
    if os.getenv('SKIP_PLUGIN_LOAD') != '1':
        register_plugins(app)

    # Import navigation manager and route utilities
    from app.utils.navigation_manager import NavigationManager
    from app.utils.route_manager import route_to_endpoint

    # Initialize template filters
    from app import template_filters
    template_filters.init_app(app)

    # Register CLI commands
    register_commands(app)

    # Make navigation manager available to templates
    @app.context_processor
    def inject_navigation():
        return {
            'navigation_manager': NavigationManager,
            'now': datetime.utcnow()
        }

    # Session expiry handler
    @app.before_request
    def check_session_expiry():
        if 'user_id' in session and session.get('_creation_time'):
            creation_time = datetime.fromtimestamp(session['_creation_time'])
            if datetime.utcnow() - creation_time > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('main.login'))

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template('400.html'), 400

    # Add WSGI middleware
    app.wsgi_app = ProxyFix(app.wsgi_app)  # Handle proxy headers

    return app
