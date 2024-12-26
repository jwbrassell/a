from flask import Flask, request, send_from_directory
from config import Config
from app.utils.vault_middleware import init_vault_middleware
from app.utils.vault_defaults import initialize_vault_policies
from app.utils.init_db import init_database
import logging
from logging.handlers import RotatingFileHandler
import os
import mimetypes
from app.extensions import login_manager, migrate
from app.models.user import User

# Import base models at module level
from app.models import *

def create_app(config_class=Config):
    # Import user model first to ensure it's registered
    from app.models.user import User
    
    # Import core models if not skipping blueprints
    if not getattr(config_class, 'SKIP_BLUEPRINTS', False):
        from app.models.role import Role
        from app.models.permission import Permission
        from app.models.permissions import Action, RoutePermission
        from app.models.navigation import NavigationCategory, PageRouteMapping
        from app.models.documents import Document, DocumentCategory, DocumentTag
        from app.models.metrics import Metric, MetricAlert, MetricDashboard
        from app.models.analytics import FeatureUsage, DocumentAnalytics, ProjectMetrics
        from app.models.dispatch import DispatchSettings, DispatchHistory
        from app.models.handoffs import WorkCenter, WorkCenterMember, HandoffSettings, Handoff
    else:
        # Always import activity models since they're needed for migrations
        from app.models.activity import UserActivity, PageVisit
    
    # Import blueprint models if not skipping blueprints
    if not getattr(config_class, 'SKIP_BLUEPRINTS', False):
        try:
            # Import AWS models
            from app.blueprints.aws_manager.models.ec2_instance import EC2Instance
            from app.blueprints.aws_manager.models.ec2_template import EC2Template
            from app.blueprints.aws_manager.models.aws_configuration import AWSConfiguration
            from app.blueprints.aws_manager.models.health_event import AWSHealthEvent

            from app.blueprints.projects.models import (
                ProjectStatus, ProjectPriority, Project, Task, Todo, Comment, History
            )
            from app.blueprints.bug_reports.models import BugReport, BugReportScreenshot
            from app.blueprints.feature_requests.models import FeatureRequest, FeatureVote, FeatureComment
            from app.blueprints.weblinks.models import WebLink, Tag, WebLinkHistory
            from app.blueprints.example.models import ExampleData

            # Only import database_reports models if not skipping vault init
            if not getattr(config_class, 'SKIP_VAULT_INIT', False):
                from app.blueprints.database_reports.models import (
                    DatabaseConnection, Report, ReportTagModel as Tag, ReportHistory
                )
        except ImportError:
            # Ignore import errors during migrations
            pass

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
    
    # Set up Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize template filters
    from app.template_filters import init_app as init_template_filters
    init_template_filters(app)
    
    # Initialize Vault middleware if not skipped
    if not app.config.get('SKIP_VAULT_MIDDLEWARE', False):
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

    # Initialize database if not skipped
    if not app.config.get('SKIP_DB_INIT', False):
        with app.app_context():
            if init_database():
                app.logger.info("Database initialized successfully")
            else:
                app.logger.error("Failed to initialize database")

    # Initialize blueprints if not skipped
    if not app.config.get('SKIP_BLUEPRINTS', False):
        with app.app_context():
            # Initialize core routes and permissions first
            if not app.config.get('SKIP_VAULT_MIDDLEWARE', False):
                try:
                    from app.routes import init_routes
                    if not init_routes(app):
                        app.logger.error("Failed to initialize core routes")
                        raise Exception("Core routes initialization failed")
                except Exception as e:
                    app.logger.error(f"Error initializing core routes: {e}")
                    raise
            else:
                try:
                    from app.routes.routes import init_base_routes
                    if not init_base_routes(app):
                        app.logger.error("Failed to initialize base routes")
                        raise Exception("Base routes initialization failed")
                except Exception as e:
                    app.logger.error(f"Error initializing base routes: {e}")
                    raise

            # Initialize admin routes first as other blueprints may depend on them
            try:
                from app.utils.add_admin_route import add_admin_routes
                if not add_admin_routes():
                    app.logger.error("Failed to initialize admin routes")
                    raise Exception("Admin routes initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing admin routes: {e}")
                raise

            # Initialize vault routes next for security
            try:
                from app.utils.add_vault_routes import add_vault_routes
                if not add_vault_routes():
                    app.logger.error("Failed to initialize vault routes")
                    raise Exception("Vault routes initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing vault routes: {e}")
                raise

            # Initialize profile module
            try:
                from app.routes.profile import init_profile
                if not init_profile(app):
                    app.logger.error("Failed to initialize profile module")
                    raise Exception("Profile module initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing profile module: {e}")
                raise

            # Initialize core blueprints
            try:
                from app.blueprints.projects import init_app as init_projects
                if not init_projects(app):
                    app.logger.error("Failed to initialize projects blueprint")
                    raise Exception("Projects blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing projects blueprint: {e}")
                raise

            # Initialize dispatch routes
            try:
                from app.utils.add_dispatch_routes import add_dispatch_routes
                if not add_dispatch_routes():
                    app.logger.error("Failed to initialize dispatch routes")
                    raise Exception("Dispatch routes initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing dispatch routes: {e}")
                raise

            # Initialize handoff routes
            try:
                from app.utils.add_handoff_routes import add_handoff_routes
                if not add_handoff_routes():
                    app.logger.error("Failed to initialize handoff routes")
                    raise Exception("Handoff routes initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing handoff routes: {e}")
                raise

            # Initialize on-call routes
            try:
                from app.utils.add_oncall_routes import add_oncall_routes
                if not add_oncall_routes():
                    app.logger.error("Failed to initialize on-call routes")
                    raise Exception("On-call routes initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing on-call routes: {e}")
                raise

            # Initialize weblinks blueprint
            try:
                from app.blueprints.weblinks import init_app as init_weblinks
                if not init_weblinks(app):
                    app.logger.error("Failed to initialize weblinks blueprint")
                    raise Exception("Weblinks blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing weblinks blueprint: {e}")
                raise

            # Initialize AWS manager blueprint
            try:
                from app.blueprints.aws_manager.plugin import init_plugin
                if not init_plugin(app):
                    app.logger.error("Failed to initialize AWS manager blueprint")
                    raise Exception("AWS manager blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing AWS manager blueprint: {e}")
                raise

            # Initialize database reports blueprint
            try:
                from app.blueprints.database_reports.plugin import init_app as init_database_reports
                if not init_database_reports(app):
                    app.logger.error("Failed to initialize database reports blueprint")
                    raise Exception("Database reports blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing database reports blueprint: {e}")
                raise

            # Initialize example plugin
            try:
                from app.utils.add_example_routes import register_example_plugin
                register_example_plugin(app)
                app.logger.info("Example plugin initialized successfully")
            except Exception as e:
                app.logger.error(f"Error initializing example plugin: {e}")
                raise

            # Initialize bug reports blueprint
            try:
                from app.blueprints.bug_reports import init_app as init_bug_reports
                if not init_bug_reports(app):
                    app.logger.error("Failed to initialize bug reports blueprint")
                    raise Exception("Bug reports blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing bug reports blueprint: {e}")
                raise

            # Initialize feature requests blueprint
            try:
                from app.blueprints.feature_requests import init_app as init_feature_requests
                if not init_feature_requests(app):
                    app.logger.error("Failed to initialize feature requests blueprint")
                    raise Exception("Feature requests blueprint initialization failed")
            except Exception as e:
                app.logger.error(f"Error initializing feature requests blueprint: {e}")
                raise

    # Initialize Vault policies and setup if not skipped
    if not app.config.get('SKIP_VAULT_MIDDLEWARE', False):
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
