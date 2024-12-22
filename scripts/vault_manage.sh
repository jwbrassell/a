#!/bin/bash
# Vault Management Script for Unix-like systems (macOS, Linux)

set -e

# Configuration
VAULT_CONFIG_DIR="/etc/vault.d"
VAULT_DATA_DIR="vault-data"
VAULT_LOG_FILE="logs/vault.log"
VAULT_AUDIT_FILE="logs/vault-audit.log"
CERT_DIR="instance/certs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure script is run with appropriate permissions
check_permissions() {
    if [ "$(id -u)" != "0" ] && [ "$1" != "status" ] && [ "$1" != "help" ]; then
        echo -e "${RED}This script must be run as root for most operations${NC}"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    echo -e "${YELLOW}Creating necessary directories...${NC}"
    mkdir -p "$VAULT_CONFIG_DIR"
    mkdir -p "$VAULT_DATA_DIR"
    mkdir -p "logs"
    mkdir -p "$CERT_DIR"
    
    # Set appropriate permissions
    chown -R vault:vault "$VAULT_DATA_DIR" 2>/dev/null || true
    chown -R vault:vault "logs" 2>/dev/null || true
    chmod 750 "$VAULT_DATA_DIR"
    chmod 750 "logs"
}

# Initialize Vault
initialize_vault() {
    echo -e "${YELLOW}Initializing Vault...${NC}"
    vault operator init -key-shares=1 -key-threshold=1 -format=json > .vault-init.json
    
    # Extract and save credentials
    TOKEN=$(jq -r '.root_token' .vault-init.json)
    UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' .vault-init.json)
    
    echo "VAULT_TOKEN=$TOKEN" > .env.vault
    echo "VAULT_UNSEAL_KEY=$UNSEAL_KEY" >> .env.vault
    
    echo -e "${GREEN}Vault initialized. Credentials saved to .env.vault${NC}"
    
    # Secure the files
    chmod 600 .env.vault
    chmod 600 .vault-init.json
}

# Start Vault
start_vault() {
    echo -e "${YELLOW}Starting Vault...${NC}"
    if [ -f /etc/systemd/system/vault.service ]; then
        systemctl start vault
    else
        vault server -config=config/vault-dev.hcl > "$VAULT_LOG_FILE" 2>&1 &
    fi
    echo -e "${GREEN}Vault started${NC}"
}

# Stop Vault
stop_vault() {
    echo -e "${YELLOW}Stopping Vault...${NC}"
    if [ -f /etc/systemd/system/vault.service ]; then
        systemctl stop vault
    else
        pkill -f "vault server" || true
    fi
    echo -e "${GREEN}Vault stopped${NC}"
}

# Restart Vault
restart_vault() {
    stop_vault
    sleep 2
    start_vault
}

# Check Vault status
status_vault() {
    echo -e "${YELLOW}Checking Vault status...${NC}"
    vault status || true
}

# Enable audit logging
enable_audit() {
    echo -e "${YELLOW}Enabling audit logging...${NC}"
    vault audit enable file file_path="$VAULT_AUDIT_FILE"
    echo -e "${GREEN}Audit logging enabled${NC}"
}

# Unseal Vault
unseal_vault() {
    if [ -f .env.vault ]; then
        source .env.vault
        echo -e "${YELLOW}Unsealing Vault...${NC}"
        vault operator unseal "$VAULT_UNSEAL_KEY"
        echo -e "${GREEN}Vault unsealed${NC}"
    else
        echo -e "${RED}No .env.vault file found${NC}"
        exit 1
    fi
}

# Clean up Vault data
cleanup() {
    echo -e "${YELLOW}Cleaning up Vault data...${NC}"
    stop_vault
    rm -rf "$VAULT_DATA_DIR"/*
    rm -f "$VAULT_LOG_FILE"
    rm -f "$VAULT_AUDIT_FILE"
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Show help
show_help() {
    echo "Vault Management Script"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start       Start Vault server"
    echo "  stop        Stop Vault server"
    echo "  restart     Restart Vault server"
    echo "  status      Show Vault status"
    echo "  init        Initialize Vault"
    echo "  unseal      Unseal Vault"
    echo "  audit       Enable audit logging"
    echo "  cleanup     Clean up Vault data"
    echo "  help        Show this help message"
}

# Main script logic
case "$1" in
    start)
        check_permissions "$1"
        create_directories
        start_vault
        ;;
    stop)
        check_permissions "$1"
        stop_vault
        ;;
    restart)
        check_permissions "$1"
        restart_vault
        ;;
    status)
        status_vault
        ;;
    init)
        check_permissions "$1"
        initialize_vault
        ;;
    unseal)
        check_permissions "$1"
        unseal_vault
        ;;
    audit)
        check_permissions "$1"
        enable_audit
        ;;
    cleanup)
        check_permissions "$1"
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

exit 0
