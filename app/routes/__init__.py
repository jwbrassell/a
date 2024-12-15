"""
Core application routes package
"""
from flask import Blueprint

main = Blueprint('main', __name__)

def init_routes(app):
    """Initialize routes after Blueprint creation to avoid circular imports"""
    # Import the routes module here to avoid circular imports
    from app.routes import routes
    
    # Register the routes with the blueprint
    routes.init_routes(main)
    
    # Register the blueprint with the app
    app.register_blueprint(main)
