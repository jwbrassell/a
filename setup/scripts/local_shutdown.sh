#!/bin/bash

# Exit on any error
set -e

echo "Starting shutdown process..."

# Check if Vault is running and stop it
if [ -f vault.pid ]; then
    VAULT_PID=$(cat vault.pid)
    if ps -p $VAULT_PID > /dev/null; then
        echo "Stopping Vault server..."
        sudo kill $VAULT_PID
        rm vault.pid
    else
        echo "Vault process not found, cleaning up pid file..."
        rm vault.pid
    fi
else
    # Try to find and kill vault process if pid file is missing
    if pgrep vault > /dev/null; then
        echo "Found running Vault process, stopping it..."
        sudo pkill vault
    fi
fi

# Clean up environment
unset VAULT_TOKEN
unset VAULT_ADDR

echo "Shutdown complete!"
echo "To start the application again, run: ./setup/scripts/local_setup.sh"
