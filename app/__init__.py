from flask import Flask
from app.extensions import init_extensions
# Import all models so Flask-Migrate can detect them
from app.models.permissions import Action, RoutePermission
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Use a minimal config if none provided
    if config_class is None:
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
        app.config['SECRET_KEY'] = "packaging-key"
    else:
        app.config.from_object(config_class)
        if hasattr(config_class, 'init_app'):
            config_class.init_app(app)

    # Initialize all extensions
    init_extensions(app)
    
    return app
