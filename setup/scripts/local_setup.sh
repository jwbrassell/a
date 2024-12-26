#!/bin/bash

# Exit on any error
set -e

# Get the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting local setup process..."

# 1. Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file with default configuration..."
    cat > .env << EOL
# Flask Configuration
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DB_TYPE=sqlite
SQLITE_PATH=instance/app.db

# Vault Configuration
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=dev-only-token

# Gunicorn Configuration
GUNICORN_ACCESS_LOG=-
GUNICORN_ERROR_LOG=-
GUNICORN_LOG_LEVEL=info
GUNICORN_PROC_NAME=portal
GUNICORN_WORKER_CLASS=sync
GUNICORN_WORKER_CONNECTIONS=1000
GUNICORN_TIMEOUT=120
GUNICORN_KEEPALIVE=5
EOL
fi

# 3. Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p instance
mkdir -p migrations
mkdir -p vault-data

# 4. Check and install Vault if needed
echo "Checking Vault installation..."
if ! command -v vault &> /dev/null; then
    echo "Vault not found. Installing Vault..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            "ubuntu"|"debian")
                # Add HashiCorp GPG key and repository
                sudo apt-get update
                sudo apt-get install -y gpg wget
                wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
                echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
                sudo apt-get update
                sudo apt-get install -y vault
                ;;
            "rhel"|"fedora"|"centos")
                # Add HashiCorp repository for RHEL-based systems
                sudo yum install -y yum-utils
                sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
                sudo yum -y install vault
                ;;
            "amzn")
                # Direct RPM download for Amazon Linux
                echo "Installing Vault on Amazon Linux..."
                ARCH=$(uname -m)
                case $ARCH in
                    x86_64)
                        VAULT_URL="https://releases.hashicorp.com/vault/1.15.4/vault_1.15.4_linux_amd64.zip"
                        ;;
                    aarch64)
                        VAULT_URL="https://releases.hashicorp.com/vault/1.15.4/vault_1.15.4_linux_arm64.zip"
                        ;;
                    *)
                        echo "Unsupported architecture: $ARCH"
                        exit 1
                        ;;
                esac
                
                # Install required packages
                sudo yum install -y unzip wget

                # Download and install Vault
                wget $VAULT_URL -O vault.zip
                unzip vault.zip
                sudo mv vault /usr/local/bin/
                rm vault.zip
                
                # Set up Vault permissions
                sudo setcap cap_ipc_lock=+ep /usr/local/bin/vault
                
                # Verify installation
                vault --version || {
                    echo "Vault installation failed"
                    exit 1
                }
                ;;
            *)
                echo "Unsupported operating system for automatic Vault installation"
                echo "Please install Vault manually from: https://www.vaultproject.io/downloads"
                exit 1
                ;;
        esac
    else
        echo "Cannot determine OS type. Please install Vault manually."
        exit 1
    fi
fi

# Start Vault server
echo "Starting Vault server..."
# Check if Vault is already running
if pgrep vault > /dev/null; then
    echo "Vault is already running. Stopping it..."
    sudo pkill vault || true
    sleep 2
fi

# Ensure logs directory has correct permissions
sudo chown -R $USER:$USER logs
sudo chmod 755 logs

# Export Vault address
export VAULT_ADDR='http://127.0.0.1:8200'

# Start Vault in dev mode
echo "Starting Vault in dev mode..."
sudo -E vault server -dev -dev-root-token-id=root > logs/vault.log 2>&1 &
VAULT_PID=$!
echo $VAULT_PID > vault.pid
echo "Waiting for Vault to start..."
sleep 10

# Export root token and verify Vault is running
export VAULT_TOKEN='root'
for i in {1..5}; do
    if vault status; then
        echo "Vault is running"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "Error: Vault failed to start. Check logs/vault.log for details"
        exit 1
    fi
    echo "Waiting for Vault to start... (attempt $i/5)"
    sleep 5
done

# Update .env with root token
sed -i.bak "s/VAULT_TOKEN=.*/VAULT_TOKEN=root/" .env

# 5. Set up database
echo "Setting up database..."
# Clean up any existing database and migrations
rm -f instance/app.db app.db
rm -rf migrations

# Initialize fresh migrations
export FLASK_APP=migrations_config.py
export SKIP_VAULT_MIDDLEWARE=true
export SKIP_VAULT_INIT=true
export SKIP_BLUEPRINTS=true

# Create instance directory if it doesn't exist
mkdir -p instance

# Initialize migrations directory
flask db init

# Create and run initial migration
flask db migrate -m "Initial database setup"
flask db upgrade

# Move database to correct location if needed
if [ -f app.db ] && [ ! -f instance/app.db ]; then
    mv app.db instance/app.db
fi

# Initialize database with data
echo "Initializing database with data..."
python init_database.py

# Verify database setup
echo "Verifying database setup..."
sqlite3 instance/app.db ".tables" || {
    echo "Error: Database tables not created properly"
    exit 1
}

# 6. Verify the setup
echo "Verifying setup..."
python3 -c "
from app import create_app
from app.models.user import User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('Error: Admin user not created')
        exit(1)
    print('Admin user verified successfully')
"

echo "Setup complete! You can now run the application with:"
echo "flask run"
echo ""
echo "Default admin credentials:"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "Vault is running in development mode with root token: 'root'"
