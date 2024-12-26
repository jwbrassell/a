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

# Configure git and update code on remote machine
echo "Configuring git and updating code..."
run_remote "sudo chown -R ec2-user:ec2-user ~/flask_app"
run_remote "cd ~/flask_app && git config --global --add safe.directory /home/ec2-user/flask_app"
run_remote "cd ~/flask_app && git remote add fluffy git@github.com:jwbrassell/a.git 2>/dev/null || true"
run_remote "cd ~/flask_app && git fetch fluffy && git checkout xmas && git pull fluffy xmas"

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

# 4. Set up Vault
echo "Setting up Vault..."
run_remote "cd ~/flask_app && bash setup/scripts/vault_linux.sh"

# 5. Run migrations and initialize database
echo "Running database migrations..."
run_remote "cd ~/flask_app && . venv/bin/activate && flask db upgrade"

echo "Initializing database and actions..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 init_database.py && python3 init_actions.py"

# 6. Initialize all blueprints and routes in correct order
echo "Initializing routes and blueprints..."
run_remote "cd ~/flask_app && . venv/bin/activate && python3 -c \"
from app import create_app
from app.utils.add_admin_route import add_admin_routes
from app.utils.add_vault_routes import add_vault_routes
from app.utils.add_database_report_routes import add_database_report_routes
from app.utils.add_project_routes import add_project_routes
from app.utils.add_dispatch_routes import add_dispatch_routes
from app.utils.add_handoff_routes import add_handoff_routes
from app.utils.add_oncall_routes import add_oncall_routes
from app.utils.add_weblinks_routes import add_weblinks_routes
from app.utils.add_example_routes import register_example_plugin
from app.blueprints.aws_manager.plugin import init_plugin
from app.blueprints.bug_reports import init_app as init_bug_reports
from app.blueprints.feature_requests import init_app as init_feature_requests

app = create_app()
with app.app_context():
    # Core routes first
    add_admin_routes()
    add_vault_routes()
    
    # Main features
    add_database_report_routes()
    add_project_routes()
    add_dispatch_routes()
    add_handoff_routes()
    add_oncall_routes()
    add_weblinks_routes()
    
    # Additional features
    register_example_plugin(app)
    init_plugin(app)
    init_bug_reports(app)
    init_feature_requests(app)
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
