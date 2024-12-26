from flask import Flask
from flask_migrate import Migrate
from app.extensions import db
from package_config import PackageConfig

app = Flask(__name__)
app.config.from_object(PackageConfig)
db.init_app(app)
migrate = Migrate(app, db)

# Import only core models needed for basic functionality
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.permissions import Action

if __name__ == '__main__':
    app.run()
