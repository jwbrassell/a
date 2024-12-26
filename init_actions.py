from app import create_app
from app.utils.init_db import init_actions
from config_migrate import MigrateConfig

app = create_app(MigrateConfig)
with app.app_context():
    init_actions()
