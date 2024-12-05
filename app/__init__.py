from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import config
import os
import logging
import sqlalchemy.exc

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def format_datetime(value):
    """Format datetime object to string."""
    if value is None:
        return ''
    return value.strftime('%Y-%m-%d %H:%M:%S')

def create_app(config_name='default'):
    """
    Flask application factory function.
    
    Args:
        config_name (str): Configuration to use (default, development, production, testing)
        
    Returns:
        Flask: Configured Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__, static_folder='static', instance_relative_config=True)
    
    # Register custom filters
    app.jinja_env.filters['datetime'] = format_datetime
    
    # Register template filters
    from . import template_filters
    template_filters.init_app(app)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app context
    init_extensions(app)
    
    # Initialize database with proper error handling
    with app.app_context():
        try:
            # Test database connection
            db.engine.connect()
            app.logger.info(f"Successfully connected to {app.config['DB_TYPE']} database")
            
            # Create all tables
            db.create_all()
            app.logger.info("Database tables created successfully")
            
            # Register blueprints including main and plugins
            from .routes import register_blueprints
            register_blueprints(app)
            
        except sqlalchemy.exc.OperationalError as e:
            app.logger.error(f"Database connection error: {str(e)}")
            if app.config['DB_TYPE'] == 'mariadb':
                app.logger.error("Failed to connect to MariaDB. Please check your database configuration.")
                app.logger.error(f"Host: {app.config['DATABASE_HOST']}")
                app.logger.error(f"Database: {app.config['DATABASE_NAME']}")
                app.logger.error(f"User: {app.config['DATABASE_USER']}")
            else:
                app.logger.error("Failed to connect to SQLite database.")
                app.logger.error(f"Path: {app.config['SQLITE_PATH']}")
            raise
            
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def init_extensions(app):
    """
    Initialize Flask extensions with the application instance.
    
    Args:
        app (Flask): Flask application instance
    """
    # Database and migrations
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Authentication and security
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'main.login'  # Specify the login view endpoint
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader callback.
        
        Args:
            user_id (str): User ID to load
            
        Returns:
            User: User object or None
        """
        from .models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

def init_plugins(app):
    """
    Initialize and load blueprint plugins.
    
    Args:
        app (Flask): Flask application instance
    """
    from .utils.plugin_manager import PluginManager
    
    # Initialize plugin manager
    plugin_manager = PluginManager(app)
    
    # Store plugin manager in app config for access in views
    app.config['PLUGIN_MANAGER'] = plugin_manager
    
    # Load all plugins
    loaded_plugins = plugin_manager.load_all_plugins()
    
    # Register plugin blueprints
    for blueprint in loaded_plugins:
        app.register_blueprint(blueprint)
        app.logger.info(f"Registered plugin blueprint: {blueprint.name}")
    
    # Log plugin loading results
    app.logger.info(f"Loaded {len(loaded_plugins)} plugins successfully")

def register_error_handlers(app):
    """
    Register error handlers for the application.
    
    Args:
        app (Flask): Flask application instance
    """
    def log_activity(user, activity):
        """Log user activity to database."""
        from .models import UserActivity
        user_activity = UserActivity(
            user_id=user.id if user else None,
            username=user.username if user else 'Anonymous',
            activity=activity
        )
        db.session.add(user_activity)
        try:
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Error logging activity: {str(e)}")
            db.session.rollback()

    def ensure_user_info():
        """Ensure user_info is available in session for authenticated users."""
        if current_user.is_authenticated:
            if 'user_info' not in session:
                from .models import User
                user = User.query.get(current_user.id)
                session['user_info'] = {
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'employee_number': user.employee_number,
                    'vzid': user.vzid
                }
            return session['user_info']
        return None

    @app.context_processor
    def inject_user_info():
        """Inject user info and navigation data into all templates."""
        from .utils.rbac import get_user_accessible_routes
        
        context = {'user_info': ensure_user_info()}
        
        if current_user.is_authenticated:
            # Get accessible routes for the current user
            context['page_route_mappings'] = get_user_accessible_routes()
            
            # Add plugin metadata to context
            plugin_manager = app.config.get('PLUGIN_MANAGER')
            if plugin_manager:
                context['plugins'] = plugin_manager.get_all_plugin_metadata()
        
        return context

    @app.errorhandler(400)
    def bad_request_error(e):
        """Handle 400 Bad Request errors, including CSRF token expiration."""
        if 'csrf' in str(e).lower():
            if current_user.is_authenticated:
                if request.method == 'GET':
                    log_activity(current_user, 'Refreshing expired CSRF token')
                    return redirect(request.url)
                else:
                    log_activity(current_user, 'Session expired (CSRF token expired)')
                    flash('Your session has expired. Please log in again to continue.', 'warning')
                    session['next_page'] = request.url
                    session.clear()
                    return redirect(url_for('main.login'))
            else:
                session['next_page'] = request.url
                flash('Please log in to continue.', 'info')
                return redirect(url_for('main.login'))

        ensure_user_info()
        return render_template('400.html'), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        """Handle 403 Forbidden errors."""
        if current_user.is_authenticated:
            log_activity(current_user, f'Attempted to access forbidden page: {request.path}')
            flash("Sorry, you don't have access to that page.", 'warning')
            ensure_user_info()
            return render_template('403.html'), 403
        else:
            session['next_page'] = request.url
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('main.login'))

    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        if current_user.is_authenticated:
            log_activity(current_user, f'Attempted to access non-existent page: {request.path}')
            flash('The page you requested does not exist.', 'warning')
            ensure_user_info()
            return render_template('404.html'), 404
        else:
            session['next_page'] = request.url
            flash('Please log in to continue.', 'info')
            return redirect(url_for('main.login'))

    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 errors."""
        error_msg = str(e)
        app.logger.error(f"Internal Server Error: {error_msg}")
        
        if current_user.is_authenticated:
            log_activity(current_user, f'Encountered server error: {error_msg}')
            ensure_user_info()
        
        db.session.rollback()
        return render_template('500.html'), 500

    @app.before_request
    def check_page_access():
        """Check if user has access to the requested page based on roles."""
        from .utils.rbac import check_route_access
        
        # Skip auth check for login page and static files
        if request.endpoint in ('main.login', 'static'):
            return

        # If user is not authenticated, store the requested URL and redirect to login
        if not current_user.is_authenticated:
            session['next_page'] = request.url
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('main.login'))

        # Ensure user_info is available for authenticated users
        ensure_user_info()

        # Check route access using RBAC utility
        if not check_route_access():
            log_activity(current_user, f'Denied access to page: {request.endpoint}')
            flash("Sorry, you don't have access to that page.", 'warning')
            return render_template('403.html'), 403
