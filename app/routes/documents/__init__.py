"""Core documents module for document management."""

from flask import Blueprint
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
documents_bp = Blueprint('documents', __name__, 
                        url_prefix='/documents',
                        template_folder='templates',
                        static_folder='static')

def init_documents(app):
    """Initialize documents module with Flask application."""
    
    # Add documents-specific configuration
    app.config.setdefault('DOCUMENTS_PER_PAGE', 20)
    app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB max file size
    
    # Register routes
    from app.routes.documents import routes
    
    # Register context processors
    register_context_processors()
    
    # Register blueprint
    app.register_blueprint(documents_bp)
    
    logger.info("Initialized documents module")

def register_context_processors():
    """Register documents-specific template context processors."""
    @documents_bp.context_processor
    def inject_documents_data():
        """Inject documents-specific data into templates."""
        return {
            'documents_version': '2.0.0'  # Hardcoded since we're no longer a plugin
        }
