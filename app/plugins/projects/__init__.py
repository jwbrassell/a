"""Projects plugin for Flask application."""
from flask import Blueprint, current_app
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.utils.plugin_manager import PluginMetadata
from .plugin import init_plugin

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Projects",
    version="1.0.0",
    description="Project management and tracking",
    author="System",
    required_roles=["admin", "user"],
    icon="fa-project-diagram",
    category="main",
    weight=10
)

bp = Blueprint('projects', __name__, template_folder='templates', static_folder='static')
logger = logging.getLogger(__name__)

def init_default_configurations(app):
    """Initialize default project configurations if they don't exist"""
    from .models import ProjectStatus, ProjectPriority
    from app.extensions import db
    
    try:
        # Check for project statuses
        if not ProjectStatus.query.first():
            logger.info("No project statuses found. Creating defaults...")
            default_statuses = [
                ('Not Started', '#dc3545'),
                ('In Progress', '#ffc107'),
                ('On Hold', '#6c757d'),
                ('Completed', '#28a745'),
                ('Cancelled', '#343a40')
            ]
            for name, color in default_statuses:
                status = ProjectStatus(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(status)
                logger.debug(f"Created status: {name}")
        
        # Check for project priorities
        if not ProjectPriority.query.first():
            logger.info("No project priorities found. Creating defaults...")
            default_priorities = [
                ('Low', '#28a745'),
                ('Medium', '#ffc107'),
                ('High', '#dc3545'),
                ('Critical', '#9c27b0')
            ]
            for name, color in default_priorities:
                priority = ProjectPriority(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(priority)
                logger.debug(f"Created priority: {name}")
        
        db.session.commit()
        logger.info("Project configurations initialized successfully")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error initializing project configurations: {str(e)}")
        # Re-raise if in debug mode
        if app.debug:
            raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project configurations: {str(e)}")
        if app.debug:
            raise

def init_app(app):
    """Initialize the projects plugin"""
    from . import routes  # Import routes after Blueprint creation
    
    # Register error handlers
    @bp.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        logger.error(f"Database error in projects plugin: {str(error)}")
        return {
            'success': False,
            'message': 'A database error occurred. Please try again later.'
        }, 500
    
    # Initialize plugin
    init_plugin(app)
    
    # Initialize configurations immediately if not in testing mode
    if not app.testing:
        with app.app_context():
            init_default_configurations(app)
    
    return bp

# Import views after Blueprint creation to avoid circular imports
from . import routes
