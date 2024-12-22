"""Configuration settings for the projects blueprint."""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Project settings
    PROJECT_NAME = os.environ.get('PROJECT_NAME', 'Flask Black Friday Lunch')
    PROJECT_UPLOAD_PATH = os.environ.get('PROJECT_UPLOAD_PATH', 'uploads/projects')
    PROJECT_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    PROJECT_MAX_CONTENT_LENGTH = int(os.environ.get('PROJECT_MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

    # Task settings
    TASK_MAX_DEPTH = int(os.environ.get('TASK_MAX_DEPTH', 3))
    TASK_ALLOW_CIRCULAR_DEPENDENCIES = os.environ.get('TASK_ALLOW_CIRCULAR_DEPENDENCIES', 'false').lower() == 'true'
    TASK_DEFAULT_LIST_POSITION = os.environ.get('TASK_DEFAULT_LIST_POSITION', 'todo')

    # Comment settings
    COMMENT_ALLOW_MARKDOWN = os.environ.get('COMMENT_ALLOW_MARKDOWN', 'true').lower() == 'true'
    COMMENT_MAX_LENGTH = int(os.environ.get('COMMENT_MAX_LENGTH', 5000))

    # Notification settings
    NOTIFICATION_EMAIL_ENABLED = os.environ.get('NOTIFICATION_EMAIL_ENABLED', 'true').lower() == 'true'
    NOTIFICATION_WEBSOCKET_ENABLED = os.environ.get('NOTIFICATION_WEBSOCKET_ENABLED', 'true').lower() == 'true'
    NOTIFICATION_DIGEST_ENABLED = os.environ.get('NOTIFICATION_DIGEST_ENABLED', 'true').lower() == 'true'
    NOTIFICATION_DIGEST_INTERVAL = int(os.environ.get('NOTIFICATION_DIGEST_INTERVAL', 24))  # hours

    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
    CACHE_KEY_PREFIX = os.environ.get('CACHE_KEY_PREFIX', 'projects_')

    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'secure-salt-here')
    SECURITY_TOKEN_MAX_AGE = int(os.environ.get('SECURITY_TOKEN_MAX_AGE', 86400))  # 24 hours

    # API settings
    API_DEFAULT_PAGE_SIZE = int(os.environ.get('API_DEFAULT_PAGE_SIZE', 20))
    API_MAX_PAGE_SIZE = int(os.environ.get('API_MAX_PAGE_SIZE', 100))
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', 100))  # requests per minute
    API_RATE_LIMIT_WINDOW = int(os.environ.get('API_RATE_LIMIT_WINDOW', 60))  # seconds

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('PERMANENT_SESSION_LIFETIME_DAYS', 31)))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 3600))  # 1 hour

    # Logging settings
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/projects.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    CACHE_TYPE = 'simple'
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Shorter session in production

    # Production-specific settings
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 10))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 20))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('SQLALCHEMY_POOL_TIMEOUT', 30))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 1800))

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
