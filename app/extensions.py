"""Flask extensions module."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from app.utils.cache_manager import cache_manager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
session = Session()
csrf = CSRFProtect()

def init_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    cache_manager.init_app(app)
    session.init_app(app)
    csrf.init_app(app)

    # Import and initialize navigation manager here to avoid circular imports
    from app.utils.navigation_manager import NavigationManager
    navigation_manager = NavigationManager()
    app.jinja_env.globals['navigation_manager'] = navigation_manager
