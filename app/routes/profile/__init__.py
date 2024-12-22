"""Core profile module for user profile management."""

from flask import Blueprint
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
profile_bp = Blueprint('profile', __name__, 
                      url_prefix='/profile',
                      template_folder='templates',
                      static_folder='static')

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DEFAULT_AVATARS = [
    '8bitsq.jpg',  # Default avatar
    'bary.jpg',
    'blackhole.jpg',
    'solarsystem.jpg',
    'stego.jpg',
    'synthsq.jpg',
    'veloci.jpg'
]

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_profile(app):
    """Initialize profile module with Flask application."""
    
    # Add profile-specific configuration
    app.config.setdefault('PROFILE_ITEMS_PER_PAGE', 10)
    
    # Import routes to register them with the blueprint
    from . import routes
    
    # Register context processors
    register_context_processors()
    
    # Register blueprint
    app.register_blueprint(profile_bp)
    
    logger.info("Initialized profile module")

def register_context_processors():
    """Register profile-specific template context processors."""
    @profile_bp.context_processor
    def inject_profile_data():
        """Inject profile-specific data into templates."""
        return {
            'profile_version': '2.0.0'  # Hardcoded since we're no longer a plugin
        }
