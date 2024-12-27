from flask import Flask
from app.extensions import init_extensions, db
from config import config

# Import all core models
from app.models.permissions import Action, RoutePermission
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

# Import all project models
from app.blueprints.projects.models import (
    Project, ProjectStatus, ProjectPriority,
    Task, Todo, Comment, History
)

# Import bug reports models
from app.blueprints.bug_reports.models import (
    BugReport, BugReportScreenshot
)

# Import feature requests models
from app.blueprints.feature_requests.models import (
    FeatureRequest, FeatureVote, FeatureComment
)

# Import weblinks models
from app.blueprints.weblinks.models import (
    WebLink, Tag, WebLinkHistory
)

# Import database reports models
from app.blueprints.database_reports.models import (
    DatabaseConnection, Report, ReportTagModel,
    ReportTag, ReportHistory
)

# Import AWS manager models
from app.blueprints.aws_manager.models import (
    AWSConfiguration, AWSHealthEvent,
    EC2Instance, EC2Template
)

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load the configuration
    if isinstance(config_name, str):
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
    else:
        app.config.from_object(config_name)
        config_name.init_app(app)

    # Initialize all extensions
    init_extensions(app)
    
    # Initialize template filters
    from app import template_filters
    template_filters.init_app(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Register all blueprints
    from app.main import routes as main_routes
    app.register_blueprint(main_routes.bp)
    
    # Register admin blueprint
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    # Register project blueprint
    from app.blueprints.projects.routes import bp as projects_bp
    app.register_blueprint(projects_bp)
    
    # Register bug reports blueprint
    from app.blueprints.bug_reports.routes import bp as bug_reports_bp
    app.register_blueprint(bug_reports_bp)
    
    # Register feature requests blueprint
    from app.blueprints.feature_requests.routes import bp as feature_requests_bp
    app.register_blueprint(feature_requests_bp)
    
    # Register database reports blueprint
    from app.blueprints.database_reports.routes import bp as database_reports_bp
    app.register_blueprint(database_reports_bp)
    
    # Register AWS manager blueprint
    from app.blueprints.aws_manager import aws_manager as aws_manager_bp
    app.register_blueprint(aws_manager_bp)
    
    # Register oncall blueprint
    from app.blueprints.oncall.routes import bp as oncall_bp
    app.register_blueprint(oncall_bp)
    
    # Register weblinks blueprint
    from app.blueprints.weblinks.routes import bp as weblinks_bp
    app.register_blueprint(weblinks_bp)
    
    # Initialize and register profile module
    from app.routes.profile import init_profile
    init_profile(app)
    
    return app
