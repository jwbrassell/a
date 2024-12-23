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

# Source environment variables from .env.vault
source "$PROJECT_ROOT/.env.vault"

# Initialize database
echo "Initializing database..."
python "$PROJECT_ROOT/init_database.py"
if [ $? -ne 0 ]; then
    echo "Database initialization failed"
    exit 1
fi

# Then run complete application setup
echo "Running application setup..."
python "$PROJECT_ROOT/setup/setup_complete.py"
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
