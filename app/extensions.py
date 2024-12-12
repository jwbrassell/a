import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

# Register PyMySQL as the MySQL driver
pymysql.install_as_MySQLdb()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

# Initialize cache with simple backend
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # Default timeout in seconds (5 minutes)
})

# Initialize CSRF protection
csrf = CSRFProtect()
