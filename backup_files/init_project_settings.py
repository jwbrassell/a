from app import create_app
from app.plugins.projects import init_app

app = create_app()
init_app(app)
print("Project settings initialized successfully")
