#!/bin/bash

# Exit on any error
set -e

# Use the flask_app directory in the user's home
APP_DIR="/home/ec2-user/flask_app"

echo "Setting up permissions for flask_app..."

# Create required directories if they don't exist
sudo mkdir -p /var/log/flask_app
sudo mkdir -p /var/run/flask_app

# Set ownership of project directory and all contents
sudo chown -R ec2-user:ec2-user "$APP_DIR"

# Set ownership of log and run directories
sudo chown -R ec2-user:ec2-user /var/log/flask_app
sudo chown -R ec2-user:ec2-user /var/run/flask_app

# Set directory permissions
sudo chmod 755 "$APP_DIR"
sudo chmod 755 /var/log/flask_app
sudo chmod 755 /var/run/flask_app

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
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl enable flask_app
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload

# Allow ec2-user to manage vault process
ec2-user ALL=(ALL) NOPASSWD: /usr/bin/pkill vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl start vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl stop vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status vault
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl enable vault

# Allow ec2-user to manage nginx
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl start nginx
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl stop nginx
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl status nginx
ec2-user ALL=(ALL) NOPASSWD: /bin/systemctl enable nginx

# Allow ec2-user to update service files
ec2-user ALL=(ALL) NOPASSWD: /bin/cp $APP_DIR/flask_app.service /etc/systemd/system/
EOF

# Set proper permissions on sudoers file
sudo chmod 440 /etc/sudoers.d/flask_app

# Verify the sudoers file syntax
sudo visudo -c

echo "Permissions setup complete!"
echo "ec2-user can now manage the flask_app service and vault process"
