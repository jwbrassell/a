#!/bin/bash

# Get the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Exit on any error
set -e

VAULT_DIR="$PROJECT_ROOT/.vault"
VAULT_VERSION="1.13.3"
VAULT_BIN="$VAULT_DIR/vault"
VAULT_CONFIG="$VAULT_DIR/config.hcl"
VAULT_DATA="$VAULT_DIR/data"
PID_FILE="$PROJECT_ROOT/vault.pid"
LOG_FILE="$PROJECT_ROOT/vault.log"
ENV_FILE="$PROJECT_ROOT/.env.vault"

# Function to clean up on error
cleanup() {
    echo "Error occurred. Cleaning up..."
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    [ -f "$LOG_FILE" ] && rm -f "$LOG_FILE"
    exit 1
}

trap cleanup ERR

# Ensure jq is installed
if ! command -v jq &> /dev/null; then
    echo "Installing jq..."
    sudo yum install -y jq
fi

echo "Setting up Vault..."

# Check if Vault is already running and accessible
if pgrep -f "vault server" > /dev/null; then
    echo "Found existing Vault process..."
    export VAULT_ADDR='http://127.0.0.1:8200'
    if "$VAULT_BIN" status >/dev/null 2>&1; then
        echo "Existing Vault is accessible, using it"
        exit 0
    else
        echo "Existing Vault is not accessible, cleaning up..."
        sudo pkill -f "vault server"
        sleep 2
    fi
fi

# Clean up any existing Vault directory
rm -rf "$VAULT_DIR"

# Create fresh directories
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

# Add Vault to PATH and set environment
echo "Setting up environment..."
export PATH="$VAULT_DIR:$PATH"
export VAULT_ADDR='http://127.0.0.1:8200'
export HOME="/home/ec2-user"  # Ensure HOME is set correctly

# Remove any existing Vault user configuration
rm -rf "$HOME/.vault"

# Start Vault with no token helper
echo "Starting Vault..."
VAULT_TOKEN="" "$VAULT_BIN" server -config="$VAULT_CONFIG" > "$LOG_FILE" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"
chmod 600 "$PID_FILE"

# Wait for Vault to start and be ready
echo "Waiting for Vault to start..."
for i in {1..30}; do
    if pgrep -f "vault server" > /dev/null; then
        # Wait for Vault API to be responsive
        for j in {1..10}; do
            if curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null 2>&1; then
                echo "Vault is running and API is responsive!"
                sleep 2  # Give it a moment to fully initialize
                break 2
            fi
            echo "Waiting for Vault API (attempt $j/10)..."
            sleep 1
        done
    fi
    if [ $i -eq 30 ]; then
        echo "Vault failed to start. Check $LOG_FILE for details."
        exit 1
    fi
    echo "Waiting for Vault to start (attempt $i/30)..."
    sleep 1
done

# Check if Vault is initialized
echo "Checking Vault initialization status..."
INIT_STATUS=$("$VAULT_BIN" status -format=json || echo '{"initialized":false,"sealed":true}')
echo "Vault status: $INIT_STATUS"
INITIALIZED=$(echo "$INIT_STATUS" | jq -r '.initialized')
SEALED=$(echo "$INIT_STATUS" | jq -r '.sealed')
echo "Initialized: $INITIALIZED"
echo "Sealed: $SEALED"

if [ "$INITIALIZED" != "true" ]; then
    echo "Vault needs initialization..."
    echo "Initializing new Vault..."
    INIT_OUTPUT=$("$VAULT_BIN" operator init -key-shares=5 -key-threshold=3 -format=json)
    
    # Extract root token and unseal keys
    ROOT_TOKEN=$(echo "$INIT_OUTPUT" | grep -o '"root_token":"[^"]*"' | cut -d'"' -f4)
    UNSEAL_KEYS=($(echo "$INIT_OUTPUT" | grep -o '"unseal_keys_hex":\[\[[^]]*\]\]' | grep -o '"[^"]*"' | sed 's/"//g'))
    
    # Save to environment file
    echo "Saving credentials to $ENV_FILE..."
    cat > "$ENV_FILE" << EOF
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=$ROOT_TOKEN
VAULT_UNSEAL_KEY_1=${UNSEAL_KEYS[0]}
VAULT_UNSEAL_KEY_2=${UNSEAL_KEYS[1]}
VAULT_UNSEAL_KEY_3=${UNSEAL_KEYS[2]}
VAULT_UNSEAL_KEY_4=${UNSEAL_KEYS[3]}
VAULT_UNSEAL_KEY_5=${UNSEAL_KEYS[4]}
EOF
    chmod 600 "$ENV_FILE"
    
    echo "Unsealing new Vault..."
    "$VAULT_BIN" operator unseal ${UNSEAL_KEYS[0]}
    "$VAULT_BIN" operator unseal ${UNSEAL_KEYS[1]}
    "$VAULT_BIN" operator unseal ${UNSEAL_KEYS[2]}
    
elif [ "$SEALED" = "true" ]; then
    echo "Vault is initialized but sealed. Checking for credentials..."
    if [ -f "$ENV_FILE" ]; then
        echo "Found existing credentials. Unsealing..."
        source "$ENV_FILE"
        "$VAULT_BIN" operator unseal $VAULT_UNSEAL_KEY_1
        "$VAULT_BIN" operator unseal $VAULT_UNSEAL_KEY_2
        "$VAULT_BIN" operator unseal $VAULT_UNSEAL_KEY_3
    else
        echo "Error: Vault is sealed and no credentials file found at $ENV_FILE"
        exit 1
    fi
else
    echo "Vault is already initialized."
fi

# Final verification
echo "Verifying Vault status..."
STATUS_OUTPUT=$("$VAULT_BIN" status -format=json)
if echo "$STATUS_OUTPUT" | grep -q '"sealed":false'; then
    echo "Success! Vault is unsealed and ready to use."
    if [ -f "$ENV_FILE" ]; then
        echo "Credentials available at: $ENV_FILE"
    fi
else
    echo "Error: Vault is still sealed. Check $LOG_FILE for details."
    exit 1
fi
