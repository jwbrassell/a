"""Configuration settings for the projects plugin."""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration settings"""
    
    # Project settings
    PROJECT_NAME = "Projects Plugin"
    PROJECT_VERSION = "1.0.0"
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'max_overflow': 2
    }
    
    # Cache settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Task settings
    MAX_TASK_DEPTH = 3
    MAX_TODOS_PER_TASK = 100
    MAX_COMMENTS_PER_TASK = 1000
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;1 per second"
    RATELIMIT_STORAGE_URL = CACHE_REDIS_URL
    
    # Monitoring settings
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
    ENABLE_QUERY_TRACKING = True
    MAX_QUERY_HISTORY = 1000
    
    # Notification settings
    ENABLE_EMAIL_NOTIFICATIONS = False
    NOTIFICATION_BATCH_SIZE = 100
    NOTIFICATION_CLEANUP_DAYS = 30
    
    # History settings
    HISTORY_RETENTION_DAYS = 90
    MAX_HISTORY_ENTRIES = 10000
    
    # API settings
    API_DEFAULT_PAGE_SIZE = 20
    API_MAX_PAGE_SIZE = 100
    API_RATE_LIMIT = "1000 per day"

class DevelopmentConfig(BaseConfig):
    """Development configuration settings"""
    
    DEBUG = True
    TESTING = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///dev.db')
    SQLALCHEMY_ECHO = True
    
    # Cache settings
    CACHE_TYPE = 'simple'
    
    # Security settings
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    
    # Monitoring settings
    ENABLE_QUERY_TRACKING = True
    
    # Email settings
    MAIL_DEBUG = True
    ENABLE_EMAIL_NOTIFICATIONS = False

class TestingConfig(BaseConfig):
    """Testing configuration settings"""
    
    DEBUG = False
    TESTING = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db')
    SQLALCHEMY_ECHO = False
    
    # Cache settings
    CACHE_TYPE = 'simple'
    
    # Security settings
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    
    # Monitoring settings
    ENABLE_QUERY_TRACKING = False
    
    # Email settings
    MAIL_SUPPRESS_SEND = True
    ENABLE_EMAIL_NOTIFICATIONS = False

class ProductionConfig(BaseConfig):
    """Production configuration settings"""
    
    DEBUG = False
    TESTING = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'max_overflow': 5
    }
    
    # Cache settings
    CACHE_REDIS_URL = os.getenv('REDIS_URL')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Monitoring settings
    ENABLE_QUERY_TRACKING = True
    SLOW_QUERY_THRESHOLD = 0.5  # stricter in production
    
    # Email settings
    ENABLE_EMAIL_NOTIFICATIONS = True
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100 per day;20 per hour;1 per second"

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    return configs.get(env, DevelopmentConfig)

# Additional configuration helpers
def init_app(app):
    """Initialize application with configuration"""
    config = get_config()
    app.config.from_object(config)
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Initialize monitoring if enabled
    if app.config['ENABLE_QUERY_TRACKING']:
        from .utils.monitoring import init_monitoring
        init_monitoring(app)
    
    # Initialize caching
    from .utils.caching import init_cache
    init_cache(app)
    
    return app
