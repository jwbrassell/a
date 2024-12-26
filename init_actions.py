from app import create_app
from app.utils.init_db import init_actions
from config import config

app = create_app(config['production'])
with app.app_context():
    init_actions()
