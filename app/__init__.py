from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
from datetime import datetime
import os
import click

# Import extensions
from app.extensions import db, login_manager, migrate

# Initialize CSRF protection
csrf = CSRFProtect()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Set configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # Initialize app-specific config

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # Initialize CSRF protection

    # Initialize image registry
    from app.utils.image_registry import ImageRegistry
    ImageRegistry.init_app(app)

    # Configure login
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import and register blueprints
    from app.routes import main as main_bp
    app.register_blueprint(main_bp)

    # Import and initialize plugin manager
    from app.utils.plugin_manager import PluginManager
    plugin_manager = PluginManager(app)
    
    # Load and register plugin blueprints within app context
    with app.app_context():
        for blueprint in plugin_manager.load_all_plugins():
            if blueprint:
                app.register_blueprint(blueprint)

    # Import navigation manager and route utilities
    from app.utils.navigation_manager import NavigationManager
    from app.utils.route_manager import route_to_endpoint

    # Initialize template filters
    from app import template_filters
    template_filters.init_app(app)

    # Make navigation manager available to templates
    @app.context_processor
    def inject_navigation():
        return {
            'navigation_manager': NavigationManager,
            'now': datetime.utcnow()
        }

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

    # Register init-db command
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with default data."""
        from app.utils.init_db import init_roles_and_users
        init_roles_and_users()
        click.echo('Initialized the database.')

    # Register fix-oncall-routes command
    from app.utils.fix_oncall_routes import fix_oncall_routes
    app.cli.add_command(fix_oncall_routes)

    return app
