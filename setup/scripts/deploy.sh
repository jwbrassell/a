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

# Configure git and update code on remote machine
echo "Configuring git and updating code..."
run_remote "sudo chown -R ec2-user:ec2-user ~/flask_app/.git"
run_remote "cd ~/flask_app && git config --global --add safe.directory /home/ec2-user/flask_app"
run_remote "cd ~/flask_app && git remote add fluffy git@github.com:jwbrassell/a.git 2>/dev/null || true"
run_remote "cd ~/flask_app && git fetch fluffy && git checkout xmas && git pull fluffy xmas"

# 1. Stop services on remote
echo "Stopping services on remote..."
run_remote "sudo systemctl stop flask_app || true"
run_remote "sudo pkill vault || true"

# 2. Set up permissions
echo "Setting up permissions..."
run_remote "cd ~/flask_app && sudo bash setup/scripts/setup_permissions.sh"

# 3. Set up Vault
echo "Setting up Vault..."
run_remote "cd ~/flask_app && bash setup/scripts/vault_linux.sh"

# 4. Update and reload systemd service
echo "Updating systemd service..."
run_remote "cd ~/flask_app && sudo cp flask_app.service /etc/systemd/system/ && sudo systemctl daemon-reload"

# 5. Start Flask application
echo "Starting Flask application..."
run_remote "sudo systemctl restart flask_app"

# 6. Check service status
echo "Checking service status..."
run_remote "sudo systemctl status flask_app"

echo "Deployment complete!"
echo "To check logs:"
echo "  Flask app logs: journalctl -u flask_app"
echo "  Vault logs: cat ~/flask_app/vault.log"
