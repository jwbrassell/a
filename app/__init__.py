from flask import Flask, render_template, redirect, url_for, flash, session
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config
from datetime import datetime
import os
import click
import sys
from werkzeug.middleware.proxy_fix import ProxyFix

# Import extensions
from app.extensions import init_extensions, db, csrf
from vault_utility import VaultUtility
from app.utils.vault_defaults import initialize_vault_structure
from app.utils.cache_manager import cached
from app.utils.alert_service import alert_service
from app.utils.metrics_collector import metrics_collector

def create_app(config_name=None, skip_session=False):
    app = Flask(__name__)
    
    # Set configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # Initialize app-specific config

    # Configure cache directory
    app.config['CACHE_DIR'] = os.path.join(app.instance_path, 'cache')
    os.makedirs(app.config['CACHE_DIR'], exist_ok=True)
    
    # Set cache configuration
    app.config.update(
        CACHE_TYPE=app.config.get('CACHE_TYPE', 'simple'),
        CACHE_DEFAULT_TIMEOUT=app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
        CACHE_THRESHOLD=app.config.get('CACHE_THRESHOLD', 1000),
        CACHE_KEY_PREFIX=app.config.get('CACHE_KEY_PREFIX', 'flask_cache_'),
        CACHE_DIR=app.config['CACHE_DIR']  # For filesystem cache
    )

    # Initialize all extensions
    init_extensions(app)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Initialize Flask-Session only if not skipped
    if not skip_session:
        from flask_session import Session
        # Configure session to use SQLAlchemy
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        app.config['SESSION_SQLALCHEMY'] = db
        Session(app)

    # Initialize logging configuration
    from app.logging_utils import init_app as init_logging
    init_logging(app)

    # Initialize image registry
    from app.utils.image_registry import ImageRegistry
    ImageRegistry.init_app(app)

    # Initialize Alert Service
    alert_service.init_app(app)

    # Initialize Metrics Collector with app context
    with app.app_context():
        metrics_collector.init_app(app)
        # Ensure metrics table exists
        from app.models.metrics import Metric
        db.create_all()

    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Changed from auth.login to main.login
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Import and register blueprints
    from app.routes import init_routes
    init_routes(app)

    # Register core modules (previously plugins)
    from app.routes.admin import init_admin
    init_admin(app)

    from app.routes.profile import init_profile
    init_profile(app)

    from app.routes.documents import init_documents
    init_documents(app)

    # Initialize request tracking middleware
    from app.utils.request_tracking import init_request_tracking
    init_request_tracking(app)

    # Import navigation manager and route utilities
    from app.utils.navigation_manager import NavigationManager
    from app.utils.route_manager import route_to_endpoint

    # Initialize template filters
    from app import template_filters
    template_filters.init_app(app)

    # Initialize Vault if not skipped
    if os.getenv('SKIP_VAULT') != '1':
        try:
            # Set FLASK_ENV for development mode
            if not os.getenv('FLASK_ENV'):
                os.environ['FLASK_ENV'] = 'development'
            
            # Initialize Vault client
            app.vault = VaultUtility(env_file_path='.env.vault')
            
            # Initialize default KV structure
            with app.app_context():
                initialize_vault_structure()
                
            app.logger.info("Successfully initialized Vault")
        except Exception as e:
            app.logger.warning(f"Running without Vault integration: {e}")
            app.vault = None
            # Set a default secret key if Vault is not available
            if not app.config.get('SECRET_KEY'):
                app.config['SECRET_KEY'] = 'development-key-no-vault'

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

    # Register error handlers with enhanced caching
    @app.errorhandler(404)
    @cached(timeout=300, key_prefix='error_404')
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    @cached(timeout=300, key_prefix='error_500')
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    @cached(timeout=300, key_prefix='error_403')
    def forbidden_error(error):
        return render_template('403.html'), 403

    @app.errorhandler(400)
    @cached(timeout=300, key_prefix='error_400')
    def bad_request_error(error):
        return render_template('400.html'), 400

    # Add WSGI middleware
    app.wsgi_app = ProxyFix(app.wsgi_app)  # Handle proxy headers

    # Register cache CLI commands
    @app.cli.group()
    def cache():
        """Cache management commands."""
        pass

    @cache.command()
    def clear():
        """Clear all caches."""
        from app.extensions import cache_manager
        cache_manager.clear_all()
        click.echo("All caches cleared.")

    @cache.command()
    def warm():
        """Warm up the cache with frequently accessed data."""
        from app.extensions import cache_manager
        cache_manager.warm_cache()
        click.echo("Cache warming completed.")

    @cache.command()
    def stats():
        """Show cache statistics."""
        from app.extensions import cache_manager
        stats = cache_manager.get_cache_stats()
        click.echo("\nCache Statistics:")
        click.echo("-" * 50)
        for cache_type, cache_stats in stats.items():
            click.echo(f"\n{cache_type}:")
            for stat, value in cache_stats.items():
                click.echo(f"  {stat}: {value}")

    return app
