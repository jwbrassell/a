#!/bin/bash

# Get the absolute path of the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Kill any existing Vault processes
echo "Cleaning up any existing Vault processes..."
pkill vault || true
sleep 2

# Create necessary directories with proper permissions
echo "Creating directories..."
mkdir -p "$PROJECT_ROOT/logs" "$PROJECT_ROOT/instance" "$PROJECT_ROOT/bin" "$PROJECT_ROOT/instance/certs"
chmod 755 "$PROJECT_ROOT/logs" "$PROJECT_ROOT/instance" "$PROJECT_ROOT/bin"
chmod 700 "$PROJECT_ROOT/instance/certs"

# Ensure SQLite directory exists with proper permissions
mkdir -p "$PROJECT_ROOT/instance"
chmod 750 "$PROJECT_ROOT/instance"

# Clean up any existing database
if [ -f "$PROJECT_ROOT/instance/app.db" ]; then
    echo "Removing existing database..."
    rm "$PROJECT_ROOT/instance/app.db"
fi

# Clean up any existing Vault data
if [ -d "$PROJECT_ROOT/vault-data" ]; then
    echo "Cleaning up existing Vault data..."
    rm -rf "$PROJECT_ROOT/vault-data"
fi

# Copy environment file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating .env file from example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
fi

# Check Python dependencies
echo "Checking Python dependencies..."
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"
if [ $? -ne 0 ]; then
    echo "Failed to install Python dependencies"
    exit 1
fi

# Run Vault setup (this will now download and install Vault if needed)
echo "Setting up Vault..."
python "$PROJECT_ROOT/setup/setup_dev_vault.py"
if [ $? -ne 0 ]; then
    echo "Vault setup failed"
    exit 1
fi

# Export Vault environment variables
export VAULT_ADDR="http://127.0.0.1:8201"
export VAULT_SKIP_VERIFY="true"

# Source environment variables from .env.vault
if [ -f "$PROJECT_ROOT/.env.vault" ]; then
    echo "Loading Vault credentials..."
    source "$PROJECT_ROOT/.env.vault"
else
    echo "Error: .env.vault file not found"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
cd "$PROJECT_ROOT"
export FLASK_APP=app.py
flask db upgrade
if [ $? -ne 0 ]; then
    echo "Database migrations failed"
    exit 1
fi

# Initialize database
echo "Initializing database..."
PYTHONPATH="$PROJECT_ROOT" python "$PROJECT_ROOT/init_database.py"
if [ $? -ne 0 ]; then
    echo "Database initialization failed"
    exit 1
fi

# Then run complete application setup
echo "Running application setup..."
PYTHONPATH="$PROJECT_ROOT" python "$PROJECT_ROOT/setup/setup_complete.py"
if [ $? -ne 0 ]; then
    echo "Application setup failed"
    exit 1
fi

echo """
Setup completed successfully!

You can now:
1. Start the Flask application:
   flask run

2. Log in with:
   Username: admin
   Password: admin

Remember to:
- Change the admin password after first login
- Monitor the logs in the logs directory

Note: If you need to reset everything and start fresh, just run this script again.
"""
