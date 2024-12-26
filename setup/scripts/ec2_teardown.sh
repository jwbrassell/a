#!/bin/bash

# EC2 connection details
EC2_USER="ec2-user"
EC2_HOST="44.220.166.165"
KEY_PATH="$HOME/.ssh/mabook.pem"

# Function to run commands on EC2
run_remote() {
    ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "$1"
}

echo "Starting EC2 environment teardown..."

# Stop and disable services
echo "Stopping services..."
run_remote "
# Stop and disable Flask app service
if systemctl is-active flask_app >/dev/null 2>&1; then
    sudo systemctl stop flask_app
    sudo systemctl disable flask_app
    echo '- Stopped Flask app service'
fi

# Stop and disable Vault service
if systemctl is-active vault >/dev/null 2>&1; then
    sudo systemctl stop vault
    sudo systemctl disable vault
    echo '- Stopped Vault service'
fi

# Stop and disable nginx
if systemctl is-active nginx >/dev/null 2>&1; then
    sudo systemctl stop nginx
    sudo systemctl disable nginx
    echo '- Stopped nginx service'
fi

# Stop and disable firewalld
if systemctl is-active firewalld >/dev/null 2>&1; then
    sudo systemctl stop firewalld
    sudo systemctl disable firewalld
    echo '- Stopped firewalld service'
fi
"

# Remove service files and configurations
echo "Removing service files and configurations..."
run_remote "
# Remove systemd service files
sudo rm -f /etc/systemd/system/flask_app.service
sudo rm -f /etc/systemd/system/vault.service
sudo systemctl daemon-reload

# Remove nginx configurations
sudo rm -f /etc/nginx/conf.d/flask_app.conf
sudo rm -rf /etc/nginx/ssl

# Clean up Vault files
rm -rf ~/.vault
rm -f ~/.env.vault
rm -f vault.pid vault.log

# Clean up Flask app directory
rm -rf ~/flask_app
"

# Clean up installed packages
echo "Cleaning up installed packages..."
run_remote "
# Remove installed packages
sudo yum remove -y nginx python3-pip python3-devel gcc openssl wget unzip curl jq firewalld

# Clean up package cache
sudo yum clean all
"

echo "Teardown complete! The following has been removed:"
echo "- All services stopped and disabled"
echo "- Service configurations removed"
echo "- Vault installation and data"
echo "- Flask application directory"
echo "- Nginx configuration and SSL certificates"
echo "- Installed packages"
