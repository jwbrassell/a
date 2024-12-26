from flask import Flask
from flask_migrate import Migrate
from app.extensions import db

# Import only core models needed for migrations
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.permissions import Action

# Create minimal Flask app for migrations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SECRET_KEY'] = "packaging-key"
db.init_app(app)
migrate = Migrate(app, db)
