#!/bin/bash

# Exit on any error
set -e

VAULT_DIR="$HOME/.vault"
VAULT_VERSION="1.13.3"
VAULT_BIN="$VAULT_DIR/vault"
VAULT_CONFIG="$VAULT_DIR/config.hcl"
VAULT_DATA="$VAULT_DIR/data"
PID_FILE="vault.pid"
LOG_FILE="vault.log"
ENV_FILE="setup/.env.vault"

# Function to clean up on error
cleanup() {
    echo "Error occurred. Cleaning up..."
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    [ -f "$LOG_FILE" ] && rm -f "$LOG_FILE"
    exit 1
}

trap cleanup ERR

# Create directories
mkdir -p "$VAULT_DIR" "$VAULT_DATA"

# Download and install Vault if not exists
if [ ! -f "$VAULT_BIN" ]; then
    echo "Downloading Vault..."
    wget -O vault.zip "https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip"
    unzip vault.zip
    mv vault "$VAULT_BIN"
    rm vault.zip
    chmod +x "$VAULT_BIN"
fi

# Create config if not exists
if [ ! -f "$VAULT_CONFIG" ]; then
    echo "Creating Vault config..."
    cat > "$VAULT_CONFIG" << EOF
storage "file" {
    path = "$VAULT_DATA"
}

listener "tcp" {
    address = "127.0.0.1:8200"
    tls_disable = 1
}

api_addr = "http://127.0.0.1:8200"
disable_mlock = true
ui = false
EOF
    chmod 600 "$VAULT_CONFIG"
fi

# Kill any existing Vault process
if [ -f "$PID_FILE" ]; then
    old_pid=$(cat "$PID_FILE")
    if kill -0 "$old_pid" 2>/dev/null; then
        echo "Stopping existing Vault process..."
        kill "$old_pid"
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# Start Vault
echo "Starting Vault..."
export VAULT_ADDR='http://127.0.0.1:8200'
"$VAULT_BIN" server -config="$VAULT_CONFIG" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
chmod 600 "$PID_FILE"

# Wait for Vault to start
echo "Waiting for Vault to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null; then
        break
    fi
    echo "Attempt $i: Vault not ready yet..."
    sleep 1
done

# Initialize Vault if needed
if ! curl -s http://127.0.0.1:8200/v1/sys/health | grep -q "initialized\":true"; then
    echo "Initializing Vault..."
    init_response=$("$VAULT_BIN" operator init -format=json -key-shares=5 -key-threshold=3)
    
    # Save credentials
    echo "Saving credentials..."
    cat > "$ENV_FILE" << EOF
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=$(echo "$init_response" | grep -o '"root_token":"[^"]*' | cut -d'"' -f4)
VAULT_UNSEAL_KEY_1=$(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | sed -n '1p')
VAULT_UNSEAL_KEY_2=$(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | sed -n '2p')
VAULT_UNSEAL_KEY_3=$(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | sed -n '3p')
VAULT_UNSEAL_KEY_4=$(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | sed -n '4p')
VAULT_UNSEAL_KEY_5=$(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | sed -n '5p')
EOF
    chmod 600 "$ENV_FILE"
    
    # Unseal Vault
    echo "Unsealing Vault..."
    for key in $(echo "$init_response" | grep -o '"keys":\[[^]]*' | grep -o '"[^"]*"' | sed 's/"//g' | head -n3); do
        "$VAULT_BIN" operator unseal "$key"
    done
fi

echo "Vault is ready!"
echo "PID: $(cat $PID_FILE)"
echo "Log file: $LOG_FILE"
echo "Environment file: $ENV_FILE"
