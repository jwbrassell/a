#!/bin/bash
set -e  # Exit on error

echo "Starting Vault setup..."

# Create necessary directories
mkdir -p vault-data logs instance
chmod 755 vault-data logs instance

# Check if Vault is already running
if curl -s http://127.0.0.1:8200/v1/sys/health > /dev/null; then
    echo "Vault is already running"
    exit 0
fi

# Set Vault address
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_SKIP_VERIFY=true

# Start Vault in background
echo "Starting Vault server..."
nohup vault server -config=config/vault-dev.hcl > logs/vault.log 2>&1 &
VAULT_PID=$!
echo $VAULT_PID > vault.pid
disown $VAULT_PID

# Wait for Vault to start
echo "Waiting for Vault to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8200/v1/sys/health > /dev/null; then
        echo "Vault is running"
        break
    fi
    echo "Waiting for Vault to start... ($i/30)"
    sleep 1
done

# Check if .env.vault exists
if [ ! -f .env.vault ]; then
    # Initialize Vault
    echo "Initializing Vault..."
    INIT_OUTPUT=$(vault operator init -key-shares=1 -key-threshold=1 -format=json)
    echo "$INIT_OUTPUT" > instance/vault-init.json
    chmod 600 instance/vault-init.json
    
    UNSEAL_KEY=$(echo "$INIT_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['unseal_keys_b64'][0])")
    ROOT_TOKEN=$(echo "$INIT_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['root_token'])")
    
    # Unseal Vault
    echo "Unsealing Vault..."
    vault operator unseal "$UNSEAL_KEY"
    
    # Save credentials
    cat > .env.vault << EOF
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=$ROOT_TOKEN
VAULT_UNSEAL_KEY=$UNSEAL_KEY
VAULT_SKIP_VERIFY=true
EOF
    chmod 600 .env.vault
    
    # Enable KV v2 secrets engine
    export VAULT_TOKEN="$ROOT_TOKEN"
    echo "Enabling KV v2 secrets engine..."
    vault secrets enable -version=2 kv
else
    echo "Using existing Vault credentials"
    source .env.vault
    vault operator unseal $VAULT_UNSEAL_KEY
fi

echo "Vault setup completed successfully"
vault status
