"""
Core application routes package
"""
from flask import Blueprint

def init_routes(app):
    """Initialize routes after Blueprint creation to avoid circular imports"""
    # Import the routes module here to avoid circular imports
    from app.routes import routes
    from app.main import bp as auth_bp
    
    # Create and register the main blueprint
    main = Blueprint('main', __name__)
    routes.init_routes(main)
    app.register_blueprint(main)
    
    # Register the auth blueprint
    app.register_blueprint(auth_bp)
