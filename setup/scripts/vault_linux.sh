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

echo "Setting up Vault..."

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
PID=$!
echo $PID > "$PID_FILE"
chmod 600 "$PID_FILE"

# Wait for Vault to start
echo "Waiting for Vault to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null; then
        echo "Vault is running!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Vault failed to start. Check $LOG_FILE for details."
        exit 1
    fi
    echo "Waiting for Vault to start (attempt $i/30)..."
    sleep 1
done

# Check if Vault is initialized
INIT_STATUS=$("$VAULT_BIN" status -format=json)
INITIALIZED=$(echo "$INIT_STATUS" | grep -o '"initialized":[^,}]*' | cut -d':' -f2)
SEALED=$(echo "$INIT_STATUS" | grep -o '"sealed":[^,}]*' | cut -d':' -f2)

if [ "$INITIALIZED" = "false" ]; then
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
    echo "Vault is already initialized and unsealed."
    if [ ! -f "$ENV_FILE" ]; then
        echo "Warning: No credentials file found at $ENV_FILE"
        echo "You'll need to provide your own credentials for Vault access."
    fi
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
