import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Register PyMySQL as the MySQL driver
pymysql.install_as_MySQLdb()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

# Remove Flask-Session initialization from here
# It will be initialized in create_app after db setup
