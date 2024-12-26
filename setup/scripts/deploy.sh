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

# 1. Push changes to git
echo "Pushing changes to git..."
git push origin main || {
    echo "Failed to push to git. Please push your changes manually and run this script again."
    exit 1
}

# 2. Stop services on remote
echo "Stopping services on remote..."
run_remote "sudo systemctl stop flask_app || true"
run_remote "sudo pkill vault || true"

# 3. Pull latest changes on remote
echo "Pulling latest changes on remote..."
run_remote "cd ~/flask_app && git pull"

# 4. Set up permissions
echo "Setting up permissions..."
run_remote "cd ~/flask_app && sudo bash setup/scripts/setup_permissions.sh"

# 5. Set up Vault
echo "Setting up Vault..."
run_remote "cd ~/flask_app && bash setup/scripts/vault_linux.sh"

# 6. Update and reload systemd service
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
