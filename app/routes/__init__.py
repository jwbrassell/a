"""
Core application routes package
"""
from flask import Blueprint

def init_routes(app):
    """Initialize routes after Blueprint creation to avoid circular imports"""
    # Import the routes module here to avoid circular imports
    from app.routes import routes
    from app.main import bp as auth_bp
    from app.routes.admin import init_app as init_admin
    from app.routes.dispatch import dispatch
    
    # Create and register the main blueprint
    main = Blueprint('main', __name__)
    routes.init_routes(main)
    app.register_blueprint(main)
    
    # Register the auth blueprint
    app.register_blueprint(auth_bp)
    
    # Initialize and register admin module
    init_admin(app)

    # Register the dispatch blueprint
    app.register_blueprint(dispatch)
