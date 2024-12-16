import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.utils.cache_manager import CacheManager, cache

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache_manager = CacheManager()
csrf = CSRFProtect()

def init_extensions(app):
    """Initialize Flask extensions."""
    # Configure cache directory
    if not app.config.get('CACHE_DIR'):
        app.config['CACHE_DIR'] = app.instance_path + '/cache'
        os.makedirs(app.config['CACHE_DIR'], exist_ok=True)
    
    # Initialize cache first
    cache.init_app(app)
    
    # Then initialize other extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    
    # Set up login manager loader
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
