#!/bin/bash
set -e  # Exit on error

echo "Starting Vault setup..."

# Create necessary directories with absolute paths
echo "Creating directories..."
VAULT_DATA="/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/vault-data"
VAULT_PLUGINS="/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/vault-plugins"
LOGS_DIR="/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/logs"
INSTANCE_DIR="/Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/instance"

mkdir -p "$VAULT_DATA" "$VAULT_PLUGINS" "$LOGS_DIR" "$INSTANCE_DIR"
chmod 755 "$VAULT_DATA" "$VAULT_PLUGINS" "$LOGS_DIR" "$INSTANCE_DIR"

# Kill any existing Vault processes
echo "Checking for existing Vault processes..."
if pgrep vault > /dev/null; then
    echo "Stopping existing Vault processes..."
    pkill vault || true
    sleep 2
fi

# Clean up any existing Vault data
echo "Cleaning up old Vault data..."
rm -rf "$VAULT_DATA"/*
rm -f "$INSTANCE_DIR/vault-init.json"
rm -f .env.vault

# Start Vault in background
echo "Starting Vault server..."
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_SKIP_VERIFY=true

# Clear any existing Vault token
unset VAULT_TOKEN

# Start Vault with direct output to see any immediate errors
nohup vault server -config=config/vault-dev.hcl > "$LOGS_DIR/vault.log" 2>&1 &
VAULT_PID=$!
disown $VAULT_PID
echo "Vault started with PID: $VAULT_PID"

# Wait for Vault to start
echo "Waiting for Vault to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8200/v1/sys/health > /dev/null; then
        echo "Vault is running"
        break
    elif ! ps -p $VAULT_PID > /dev/null; then
        echo "Vault process died. Check logs/vault.log for details"
        cat "$LOGS_DIR/vault.log"
        exit 1
    fi
    echo "Attempt $i: Waiting for Vault to start..."
    sleep 1
done

# Initialize Vault and capture output
echo "Initializing Vault..."
INIT_OUTPUT=$(vault operator init -key-shares=1 -key-threshold=1 -format=json)

# Save initialization output
echo "$INIT_OUTPUT" > "$INSTANCE_DIR/vault-init.json"
chmod 600 "$INSTANCE_DIR/vault-init.json"

# Extract keys using jq-style parsing
UNSEAL_KEY=$(echo "$INIT_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['unseal_keys_b64'][0])")
ROOT_TOKEN=$(echo "$INIT_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['root_token'])")

# Unseal Vault using the key directly
echo "Unsealing Vault..."
curl -X PUT -d "{\"key\": \"$UNSEAL_KEY\"}" http://127.0.0.1:8200/v1/sys/unseal

# Save credentials
echo "Saving credentials..."
cat > .env.vault << EOF
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=$ROOT_TOKEN
VAULT_UNSEAL_KEY=$UNSEAL_KEY
VAULT_SKIP_VERIFY=true
EOF
chmod 600 .env.vault

# Export token for subsequent commands
export VAULT_TOKEN="$ROOT_TOKEN"

# Enable KV v2 secrets engine
echo "Enabling KV v2 secrets engine..."
vault secrets enable -version=2 kv

# Save PID
echo $VAULT_PID > vault.pid
echo "Vault setup completed successfully"

# Final status check
vault status

# Verify token works
vault token lookup

# List enabled secrets engines
vault secrets list
