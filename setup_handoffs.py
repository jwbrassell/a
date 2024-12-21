from app import create_app
from app.utils.add_handoff_routes import add_handoff_routes

app = create_app()
with app.app_context():
    add_handoff_routes()
