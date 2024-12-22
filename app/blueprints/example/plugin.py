from flask import current_app
from app.utils.route_manager import map_route_to_roles

class ExamplePlugin:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        from . import example
        app.register_blueprint(example, url_prefix='/example')
        
        # Register route with the route manager
        map_route_to_roles(
            route_path='/example',
            page_name='Example Plugin',
            roles=['admin'],  # Default to admin only
            category_id='Tools',
            icon='fa-chart-bar',  # Using chart icon since this is a data visualization plugin
            weight=0
        )
