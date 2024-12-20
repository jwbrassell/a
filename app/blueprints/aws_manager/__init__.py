from flask import Blueprint

# Create blueprint
aws_manager = Blueprint(
    'aws_manager',
    __name__,
    url_prefix='/aws',
    template_folder='templates',
    static_folder='static'
)

# Import routes after blueprint creation to avoid circular imports
from . import routes

# Import and initialize plugin
from .plugin import init_plugin

def init_app(app):
    """Initialize AWS manager blueprint"""
    # Register blueprint first
    app.register_blueprint(aws_manager)
    
    # Add template context processor for breadcrumbs
    from .plugin import get_breadcrumb_data
    
    @aws_manager.context_processor
    def inject_breadcrumbs():
        def get_breadcrumbs(**kwargs):
            return get_breadcrumb_data(aws_manager.name, **kwargs)
        return dict(get_breadcrumbs=get_breadcrumbs)
    
    # Add error handlers
    @aws_manager.errorhandler(404)
    def handle_404(error):
        return {
            'error': 'Not Found',
            'message': str(error)
        }, 404

    @aws_manager.errorhandler(400)
    def handle_400(error):
        return {
            'error': 'Bad Request',
            'message': str(error)
        }, 400

    @aws_manager.errorhandler(500)
    def handle_500(error):
        return {
            'error': 'Internal Server Error',
            'message': str(error)
        }, 500
    
    # Initialize plugin after routes are registered
    init_plugin(app)
    
    return True
