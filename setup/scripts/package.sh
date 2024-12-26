#!/bin/bash

# Exit on any error
set -e

echo "Starting application packaging process..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create a temporary config for packaging
cat > package_config.py << 'EOL'
class PackageConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SKIP_VAULT_MIDDLEWARE = True
    SKIP_VAULT_INIT = True
    SKIP_BLUEPRINTS = True  # Skip all blueprints during packaging
    SECRET_KEY = "packaging-key"
    
    @staticmethod
    def init_app(app):
        pass

EOL

# Create temporary files for packaging and migrations
cat > temp_init.py << 'EOL'
from flask import Flask
from app.extensions import db

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Use a minimal config if none provided
    if config_class is None:
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
        app.config['SECRET_KEY'] = "packaging-key"
    else:
        app.config.from_object(config_class)
        if hasattr(config_class, 'init_app'):
            config_class.init_app(app)

    # Only initialize database
    db.init_app(app)
    
    return app

EOL

cat > temp_app.py << 'EOL'
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
EOL

# Initialize fresh migrations
rm -rf migrations
mkdir -p migrations
export FLASK_APP=migrations_config.py
flask db init
flask db migrate -m "Initial migration"

# Create migrations directory in dist
mkdir -p dist/migrations
cp -r migrations/* dist/migrations/

# Clean up temporary files
rm temp_app.py package_config.py

# Backup original __init__.py
cp app/__init__.py app/__init__.py.bak

# Replace with minimal version for packaging
cp temp_init.py app/__init__.py

# Create a database initialization script that doesn't require Vault
cat > package_init_db.py << 'EOL'
from app import create_app
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.models.permissions import Action
from datetime import datetime

def package_init_database():
    # Use the minimal app
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default actions
        default_actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access')
        ]
        
        for name, method, desc in default_actions:
            if not Action.query.filter_by(name=name).first():
                action = Action(name=name, method=method, description=desc)
                db.session.add(action)
        
        # Create admin role
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            admin_role = Role(
                name='Administrator',
                description='Full system access',
                is_system_role=True
            )
            db.session.add(admin_role)
        
        # Create initial admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_active=True
            )
            admin_user.set_password('admin')
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
        
        try:
            db.session.commit()
            print("Package database initialized successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing package database: {e}")
            return False

if __name__ == '__main__':
    package_init_database()
EOL

# Run the package database initialization
python package_init_db.py

echo "Creating distribution directory..."
mkdir -p dist

# Restore original __init__.py
mv app/__init__.py.bak app/__init__.py


# Copy necessary files to dist
cp -r app dist/
cp temp_init.py dist/app/__init__.py  # Use minimal init.py in dist
cp app/__init__.py dist/app/__init__.py.bak  # Copy original init.py as backup
cp -r migrations dist/
cp -r config dist/
cp -r setup dist/
cp requirements.txt dist/
cp wsgi.py dist/
cp package_init_db.py dist/
cp migrations_config.py dist/
cp flask_app.service dist/
cp vault_utility.py dist/

# Create a script to handle app restoration
cat > dist/restore_app.sh << 'EOL'
#!/bin/bash
set -e

# Backup minimal init.py and restore full version
cp app/__init__.py app/__init__.py.minimal
cp app/__init__.py.bak app/__init__.py

echo "Full application restored successfully"
EOL

# Make restore script executable
chmod +x dist/restore_app.sh

echo "Package created successfully in dist/ directory"
echo "You can now deploy the contents of the dist/ directory"
