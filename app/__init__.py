from flask import Flask
from app.extensions import init_extensions
from config import config
# Import all models so Flask-Migrate can detect them
from app.models.permissions import Action, RoutePermission
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load the configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize all extensions
    init_extensions(app)
    
    return app
