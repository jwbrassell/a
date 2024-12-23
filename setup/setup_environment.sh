#!/bin/bash

# Setup script for complete environment initialization

# Create necessary directories with proper permissions
echo "Creating directories..."
mkdir -p logs instance bin
chmod 755 logs instance bin

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Run Vault setup (this will now download and install Vault if needed)
echo "Setting up Vault..."
python setup/setup_dev_vault.py
if [ $? -ne 0 ]; then
    echo "Vault setup failed"
    exit 1
fi

# Source environment variables from .env.vault
source .env.vault

# Initialize database
echo "Initializing database..."
python init_database.py
if [ $? -ne 0 ]; then
    echo "Database initialization failed"
    exit 1
fi

# Then run complete application setup
echo "Running application setup..."
python setup/setup_complete.py
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
