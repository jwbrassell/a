import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_redis import FlaskRedis
import ssl

# Register PyMySQL as the MySQL driver
pymysql.install_as_MySQLdb()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

# Initialize Redis with SSL support
class SSLRedis(FlaskRedis):
    def init_app(self, app):
        ssl_context = None
        if app.config.get('REDIS_SSL', False):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Allow self-signed certificates
            
            # Load certificates if provided
            if app.config.get('REDIS_SSL_CA_CERTS'):
                ssl_context.load_verify_locations(app.config['REDIS_SSL_CA_CERTS'])
            if app.config.get('REDIS_SSL_CERTFILE') and app.config.get('REDIS_SSL_KEYFILE'):
                ssl_context.load_cert_chain(
                    app.config['REDIS_SSL_CERTFILE'],
                    app.config['REDIS_SSL_KEYFILE']
                )

        super().init_app(
            app,
            ssl=ssl_context,
            ssl_cert_reqs=None  # We handle cert requirements in the ssl_context
        )

redis_client = SSLRedis()

# Initialize cache with Redis backend
cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': None,  # Will be set from app config in create_app
    'CACHE_DEFAULT_TIMEOUT': 300  # Default timeout in seconds (5 minutes)
})

# Remove Flask-Session initialization from here
# It will be initialized in create_app after db setup
