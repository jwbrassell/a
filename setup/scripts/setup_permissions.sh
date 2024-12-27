#!/bin/bash

# Exit on any error
set -e

# Get the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Setting up permissions for flask_app..."

# Create required directories if they don't exist
sudo mkdir -p /var/log/flask_app
sudo mkdir -p /var/run/flask_app

# Set ownership of project directory and all contents
sudo chown -R ec2-user:ec2-user "$PROJECT_ROOT"

# Set ownership of log and run directories
sudo chown -R ec2-user:ec2-user /var/log/flask_app
sudo chown -R ec2-user:ec2-user /var/run/flask_app

# Set directory permissions
sudo chmod 755 "$PROJECT_ROOT"
sudo chmod 755 /var/log/flask_app
sudo chmod 755 /var/run/flask_app

# Set up instance directory and SQLite database permissions
sudo mkdir -p "$PROJECT_ROOT/instance"
sudo chown -R ec2-user:ec2-user "$PROJECT_ROOT/instance"
sudo chmod 775 "$PROJECT_ROOT/instance"

# Create SQLite database directory if it doesn't exist
sudo mkdir -p "$PROJECT_ROOT/instance"
if [ -f "$PROJECT_ROOT/instance/app.db" ]; then
    sudo chmod 664 "$PROJECT_ROOT/instance/app.db"
fi

# Set permissions for environment files
if [ -f "$PROJECT_ROOT/.env" ]; then
    sudo chmod 600 "$PROJECT_ROOT/.env"
    sudo chown ec2-user:ec2-user "$PROJECT_ROOT/.env"
fi
if [ -f "$PROJECT_ROOT/.env.vault" ]; then
    sudo chmod 600 "$PROJECT_ROOT/.env.vault"
    sudo chown ec2-user:ec2-user "$PROJECT_ROOT/.env.vault"
fi

# Add ec2-user to necessary groups
sudo usermod -aG systemd-journal ec2-user

# Create sudoers file for flask_app
echo "Creating sudoers file for flask_app..."
sudo tee /etc/sudoers.d/flask_app << EOF
# Allow ec2-user to manage flask_app service without password
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl start flask_app
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl stop flask_app
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart flask_app
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status flask_app

# Allow ec2-user to manage vault process
ec2-user ALL=(ALL) NOPASSWD: /usr/bin/pkill vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload

# Allow ec2-user to update service file
ec2-user ALL=(ALL) NOPASSWD: /bin/cp $PROJECT_ROOT/flask_app.service /etc/systemd/system/
EOF

# Set proper permissions on sudoers file
sudo chmod 440 /etc/sudoers.d/flask_app

# Verify the sudoers file syntax
sudo visudo -c

echo "Permissions setup complete!"
echo "ec2-user can now manage the flask_app service and vault process"
