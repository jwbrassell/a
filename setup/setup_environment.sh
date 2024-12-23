#!/bin/bash

# Get the absolute path of the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Create necessary directories with proper permissions
echo "Creating directories..."
mkdir -p "$PROJECT_ROOT/logs" "$PROJECT_ROOT/instance" "$PROJECT_ROOT/bin"
chmod 755 "$PROJECT_ROOT/logs" "$PROJECT_ROOT/instance" "$PROJECT_ROOT/bin"

# Copy environment file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating .env file from example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
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
"""
