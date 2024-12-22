#!/bin/bash

# Setup script for complete environment initialization

# Create necessary directories with proper permissions
echo "Creating directories..."
mkdir -p vault-data vault-plugins logs instance
chmod 755 vault-data vault-plugins logs instance

# Kill any existing Vault processes
echo "Cleaning up existing Vault processes..."
pkill vault
sleep 2

# Start Vault in background
echo "Starting Vault server..."
export VAULT_ADDR='http://127.0.0.1:8200'
nohup vault server -config=config/vault-dev.hcl > logs/vault.log 2>&1 &
VAULT_PID=$!

# Wait for Vault to start
echo "Waiting for Vault to start..."
sleep 5

# Initialize Vault if needed
if ! vault status > /dev/null 2>&1; then
    echo "Initializing Vault..."
    vault operator init -key-shares=1 -key-threshold=1 -format=json > instance/vault-init.json
    chmod 600 instance/vault-init.json
    
    # Extract keys
    UNSEAL_KEY=$(cat instance/vault-init.json | grep -o '"unseal_keys_b64":\["[^"]*' | cut -d'"' -f4)
    ROOT_TOKEN=$(cat instance/vault-init.json | grep -o '"root_token":"[^"]*' | cut -d'"' -f4)
    
    # Unseal Vault
    vault operator unseal $UNSEAL_KEY
    
    # Update .env.vault
    echo "VAULT_ADDR=http://127.0.0.1:8200" > .env.vault
    echo "VAULT_TOKEN=$ROOT_TOKEN" >> .env.vault
    echo "VAULT_UNSEAL_KEY=$UNSEAL_KEY" >> .env.vault
    chmod 600 .env.vault
else
    echo "Vault is already initialized"
fi

# Export Vault token for subsequent commands
export VAULT_TOKEN=$(grep VAULT_TOKEN .env.vault | cut -d'=' -f2)

# Initialize database
echo "Initializing database..."
python init_db.py

# Then run complete application setup
echo "Running application setup..."
python setup_complete.py
if [ $? -ne 0 ]; then
    echo "Application setup failed"
    exit 1
fi

# Run verification if available
if [ -f "utils/setup/verify_deployment.py" ]; then
    echo "Running verification..."
    python utils/setup/verify_deployment.py
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
- Keep the Vault credentials secure (in instance/vault-init.json and .env.vault)
- Change the admin password after first login
- Monitor the logs in the logs directory
"""
