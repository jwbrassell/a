from app import create_app
from app.utils.add_dispatch_routes import add_dispatch_routes

app = create_app()
with app.app_context():
    add_dispatch_routes()
