import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import request

load_dotenv()

class Config:
    """Base configuration class."""
    
    # Security configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    WTF_CSRF_ENABLED = True
    
    # Database configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # Default to SQLite if not specified
    
    # MariaDB configuration
    DATABASE_USER = os.getenv('DATABASE_USER', 'flask_app_user')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'default_password')
    DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'portal_db')
    
    # SQLite configuration
    SQLITE_PATH = os.getenv('SQLITE_PATH', 'instance/app.db')
    
    # Flask-Caching configuration
    CACHE_TYPE = 'simple'  # Use simple cache for development
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = 1000
    CACHE_KEY_PREFIX = 'flask_cache_'
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_SQLALCHEMY = None  # Will be set in init_app
    SESSION_SQLALCHEMY_TABLE = 'flask_sessions'
    SESSION_USE_SIGNER = True
    SESSION_FILE_THRESHOLD = 500
    
    # Static file configuration
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year in seconds
    STATIC_CACHE_TIMEOUT = 2592000  # 30 days in seconds
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join('instance', 'uploads')
    
    # Cache timeouts for specific file types
    FONT_CACHE_TIMEOUT = 31536000  # 1 year for fonts
    IMAGE_CACHE_TIMEOUT = 2592000   # 30 days for images
    
    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 30,  # Increased pool size for better performance
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 10,  # Allow more overflow connections
        'pool_timeout': 20,  # Reduced timeout
        'echo': False,  # Disable SQL echoing for better performance
        'pool_use_lifo': True,  # Use LIFO to reduce thread contention
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration."""
        instance_path = os.path.join(app.root_path, 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Set instance path in app config
        app.instance_path = instance_path
        
        # Ensure proper permissions on instance directory
        os.chmod(instance_path, 0o755)
        
        # Create uploads directory
        uploads_dir = os.path.join(instance_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        os.chmod(uploads_dir, 0o755)
        
        # Create cache directory if using filesystem cache
        cache_dir = os.path.join(instance_path, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        os.chmod(cache_dir, 0o755)
        
        # Set database URI based on configuration
        if app.config['DB_TYPE'] == 'mariadb':
            app.config['SQLALCHEMY_DATABASE_URI'] = (
                f'mysql+pymysql://{app.config["DATABASE_USER"]}:'
                f'{app.config["DATABASE_PASSWORD"]}@'
                f'{app.config["DATABASE_HOST"]}/'
                f'{app.config["DATABASE_NAME"]}?charset=utf8mb4'
            )
            app.logger.info("Using MariaDB configuration")
        else:
            # Ensure SQLite directory exists
            sqlite_path = os.path.join(app.root_path, app.config['SQLITE_PATH'])
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
            app.logger.info("Using SQLite configuration")
        
        # Set SESSION_SQLALCHEMY after db is initialized
        from app.extensions import db
        app.config['SESSION_SQLALCHEMY'] = db

        # Add security and cache headers
        @app.after_request
        def add_security_headers(response):
            # Security Headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy with explicit CSS allowance
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' http: https:; "  # Allow CSS from any source
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' http: https:; "
                "frame-ancestors 'self'; "
                "form-action 'self'; "
                "base-uri 'self'; "
                "object-src 'none'"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # Set correct MIME types for static files
            if request.path.endswith('.css'):
                response.headers['Content-Type'] = 'text/css; charset=utf-8'
            elif request.path.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
            
            # Enhanced cache headers for static files
            if 'static' in request.path:
                # Set ETag for all static files
                response.add_etag()
                
                # Set cache timeout based on file type
                if any(ext in request.path.lower() for ext in ['.woff', '.woff2', '.ttf', '.eot']):
                    # Font files get longest cache time
                    response.cache_control.max_age = app.config['FONT_CACHE_TIMEOUT']
                    response.cache_control.public = True
                    response.cache_control.immutable = True
                elif any(ext in request.path.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    # Images get medium cache time
                    response.cache_control.max_age = app.config['IMAGE_CACHE_TIMEOUT']
                    response.cache_control.public = True
                    response.cache_control.must_revalidate = True
                else:
                    # Other static files use default cache timeout
                    response.cache_control.max_age = app.config['STATIC_CACHE_TIMEOUT']
                    response.cache_control.public = True
                    response.cache_control.must_revalidate = True
            
            return response

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    CACHE_TYPE = 'simple'  # Use simple cache for development
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Setup development-specific logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_TYPE = 'null'  # Disable caching in testing
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Setup testing-specific logging
        import logging
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    CACHE_TYPE = 'filesystem'  # Use filesystem cache in production
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Add HSTS header only in production
        @app.after_request
        def add_hsts_header(response):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
        
        # Production logging configuration
        import logging
        from logging.handlers import SysLogHandler
        
        # Setup syslog handler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
        syslog_handler.setFormatter(formatter)
        app.logger.addHandler(syslog_handler)
        
        # Set production log level
        app.logger.setLevel(logging.WARNING)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
