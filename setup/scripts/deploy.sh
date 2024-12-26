#!/bin/bash

# Exit on any error
set -e

# EC2 connection details
EC2_USER="ec2-user"
EC2_HOST="44.220.166.165"
KEY_PATH="$HOME/.ssh/mabook.pem"

# Get the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to run commands on EC2
run_remote() {
    ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "$1"
}

# Function to copy files to EC2
copy_to_remote() {
    scp -i "$KEY_PATH" -r "$1" "$EC2_USER@$EC2_HOST:$2"
}

echo "Starting deployment process..."

# Set up SSH for git
echo "Setting up SSH for git..."
run_remote "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
run_remote "ssh-keyscan github.com >> ~/.ssh/known_hosts"
copy_to_remote "$HOME/.ssh/id_ed25519" "~/.ssh/"
copy_to_remote "$HOME/.ssh/id_ed25519.pub" "~/.ssh/"
run_remote "chmod 600 ~/.ssh/id_ed25519*"

# Package the application locally
echo "Packaging application..."
bash "$SCRIPT_DIR/package.sh"

# Copy packaged files to remote
echo "Copying packaged files to remote..."
run_remote "rm -rf ~/flask_app/*"  # Clean existing files
copy_to_remote "dist/*" "~/flask_app/"
run_remote "sudo chown -R ec2-user:ec2-user ~/flask_app"

# 1. Stop services on remote
echo "Stopping services on remote..."
run_remote "sudo systemctl stop flask_app || true"
run_remote "sudo pkill vault || true"

# 2. Install Python dependencies
echo "Installing Python dependencies..."
run_remote "cd ~/flask_app && rm -rf venv && python3 -m venv venv && . venv/bin/activate && venv/bin/pip install --upgrade pip && venv/bin/pip install -r requirements.txt"

# 3. Set up permissions
echo "Setting up permissions..."
run_remote "cd ~/flask_app && sudo bash setup/scripts/setup_permissions.sh"

# 4. Set up database using minimal app
echo "Cleaning existing database..."
run_remote "cd ~/flask_app && rm -f app.db"

echo "Setting up database..."
run_remote "cd ~/flask_app && . venv/bin/activate && rm -rf migrations && mkdir -p migrations && cp -r dist/migrations/* migrations/ && SKIP_VAULT_MIDDLEWARE=true SKIP_VAULT_INIT=true SKIP_BLUEPRINTS=true FLASK_APP=migrations_config.py flask db stamp head && SKIP_VAULT_MIDDLEWARE=true SKIP_VAULT_INIT=true SKIP_BLUEPRINTS=true FLASK_APP=migrations_config.py flask db upgrade"

# Initialize database with packaged script
echo "Initializing database with packaged data..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 package_init_db.py"

# Verify database setup with minimal app
echo "Verifying database setup..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 -c \"
from app import create_app
from app.models.user import User
from app.models.role import Role

app = create_app()
with app.app_context():
    # Verify admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin or not admin.roles:
        raise Exception('Database verification failed: Admin user not properly initialized')
    print('Database verification successful')
\""

# 5. Set up Vault and restore full app
echo "Setting up Vault..."
run_remote "cd ~/flask_app && bash setup/scripts/vault_linux.sh"

# Restore full app version
echo "Restoring full app..."
run_remote "cd ~/flask_app && chmod +x restore_app.sh && ./restore_app.sh && rm -f app/__init__.py.minimal"

# 6. Initialize routes and blueprints
echo "Initializing application..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 -c \"
from app import create_app
app = create_app()
print('Application initialized successfully')
\""

# 7. Verify all routes are registered
echo "Verifying route initialization..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 -c \"
from app import create_app
app = create_app()
with app.app_context():
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    print('Registered routes:', len(routes))
    if len(routes) < 50:  # We expect more than 50 routes in a fully initialized app
        raise Exception('Not all routes were registered')
\""

# 8. Update and reload systemd service
echo "Updating systemd service..."
run_remote "cd ~/flask_app && sudo cp flask_app.service /etc/systemd/system/ && sudo systemctl daemon-reload"

# 7. Start Flask application
echo "Starting Flask application..."
run_remote "sudo systemctl restart flask_app"

# 8. Check service status
echo "Checking service status..."
run_remote "sudo systemctl status flask_app"

echo "Deployment complete!"
echo "To check logs:"
echo "  Flask app logs: journalctl -u flask_app"
echo "  Vault logs: cat ~/flask_app/vault.log"
