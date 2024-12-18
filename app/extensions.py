from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
import os

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
session = Session()

# Initialize cache with default settings
cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Initialize CacheManager with the same cache instance
class CacheManager:
    def __init__(self):
        self.memory_cache = cache

cache_manager = CacheManager()

def init_extensions(app):
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app)
    csrf.init_app(app)
    session.init_app(app)
    
    # Initialize cache with app's config
    app.config.setdefault('CACHE_TYPE', 'simple')
    app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)
    cache.init_app(app)
    
    # Configure login
    login.login_view = 'auth.login'
    login.login_message = 'Please log in to access this page.'
    login.login_message_category = 'info'

    @login.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
