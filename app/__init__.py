from flask import Flask
from app.extensions import db

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

    # Only initialize database
    db.init_app(app)
    
    return app

