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
    
    # Initialize admin module
    from app.routes.admin import init_app as init_admin_module
    init_admin_module(app)
    
    # Register project blueprint
    from app.blueprints.projects.routes import bp as projects_bp
    app.register_blueprint(projects_bp)
    
    # Initialize bug reports plugin
    from app.blueprints.bug_reports.plugin import init_app as init_bug_reports
    init_bug_reports(app)
    
    # Initialize example plugin
    from app.utils.add_example_routes import register_example_plugin
    register_example_plugin(app)
    
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
    
    # Register dispatch routes
    from app.routes.dispatch import dispatch
    app.register_blueprint(dispatch)
    from app.utils.add_dispatch_routes import add_dispatch_routes
    add_dispatch_routes()
    
    # Initialize and register documents module
    from app.routes.documents import init_documents
    init_documents(app)
    from app.utils.add_document_routes import add_document_routes
    add_document_routes()
    
    # Register handoff routes
    from app.routes.handoffs import handoffs
    app.register_blueprint(handoffs)
    from app.utils.add_handoff_routes import add_handoff_routes
    add_handoff_routes()
    
    return app
