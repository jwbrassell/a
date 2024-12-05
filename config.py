import os
from dotenv import load_dotenv

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
    
    # Session configuration
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours
    SESSION_USE_SIGNER = True
    SESSION_FILE_THRESHOLD = 500
    
    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Vault configuration
    VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://localhost:8200')
    VAULT_TOKEN = os.getenv('VAULT_TOKEN')

    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    @staticmethod
    def init_app(app):
        """Initialize application configuration."""
        instance_path = os.path.join(app.root_path, 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Set instance path in app config
        app.instance_path = instance_path
        
        # Ensure proper permissions on instance directory
        os.chmod(instance_path, 0o755)
        
        # Set database URI based on configuration
        if app.config['DB_TYPE'] == 'mariadb':
            app.config['SQLALCHEMY_DATABASE_URI'] = (
                f'mysql+pymysql://{app.config["DATABASE_USER"]}:'
                f'{app.config["DATABASE_PASSWORD"]}@'
                f'{app.config["DATABASE_HOST"]}/'
                f'{app.config["DATABASE_NAME"]}'
            )
            app.logger.info("Using MariaDB configuration")
        else:
            # Ensure SQLite directory exists
            sqlite_path = app.config['SQLITE_PATH']
            os.makedirs(os.path.dirname(os.path.join(app.root_path, sqlite_path)), exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
            app.logger.info("Using SQLite configuration")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Setup development-specific logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        
        # Log database configuration
        app.logger.info(f"Using database type: {app.config['DB_TYPE']}")
        app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Always use in-memory SQLite for testing
    
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
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
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
        
        # Log database configuration
        app.logger.info(f"Using database type: {app.config['DB_TYPE']}")
        if app.config['DB_TYPE'] == 'mariadb':
            app.logger.info(f"Database host: {app.config['DATABASE_HOST']}")
            app.logger.info(f"Database name: {app.config['DATABASE_NAME']}")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
