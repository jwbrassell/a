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

# 4. Start Vault server in development mode
echo "Starting Vault server..."
# Check if Vault is already running
if pgrep vault > /dev/null; then
    echo "Vault is already running. Stopping it..."
    pkill vault
    sleep 2
fi

# Start Vault in background
vault server -config config/vault-dev.hcl > logs/vault.log 2>&1 &
echo $! > vault.pid
echo "Waiting for Vault to start..."
sleep 5

# Export Vault development token
export VAULT_TOKEN=dev-only-token
export VAULT_ADDR=http://localhost:8200

# Initialize Vault
vault operator init -key-shares=1 -key-threshold=1 > logs/vault_init.txt
UNSEAL_KEY=$(grep "Unseal Key 1:" logs/vault_init.txt | awk '{print $4}')
ROOT_TOKEN=$(grep "Initial Root Token:" logs/vault_init.txt | awk '{print $4}')

# Unseal Vault
vault operator unseal $UNSEAL_KEY

# Update .env with actual Vault token
sed -i.bak "s/VAULT_TOKEN=.*/VAULT_TOKEN=$ROOT_TOKEN/" .env

# 5. Initialize database
echo "Initializing database..."
flask db upgrade
python init_database.py

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
echo "Vault is running in development mode. Root token is saved in logs/vault_init.txt"
