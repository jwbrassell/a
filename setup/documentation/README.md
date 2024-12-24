# Vault Integration Setup

This directory contains scripts and documentation for setting up HashiCorp Vault integration with the Flask application. The setup process is designed to work on both macOS and Linux (CentOS/Rocky) systems.

## Prerequisites

### macOS
- Homebrew must be installed (https://brew.sh)
- Python 3.x
- Python packages: `requests`, `python-dotenv`

### Linux (CentOS/Rocky)
- sudo access
- Python 3.x
- Python packages: `requests`, `python-dotenv`

## Scripts Overview

### 1. vault_setup.py
Initial setup script that:
- Detects the operating system (macOS or CentOS/Rocky Linux)
- Downloads and installs Vault appropriate for the OS
- Configures Vault for local development/production
- Initializes Vault and saves unseal keys
- Starts the Vault server

Usage:
```bash
python3 setup/scripts/vault_setup.py
```

This creates `setup/.env.vault` containing:
- VAULT_ADDR
- VAULT_TOKEN (root token)
- VAULT_UNSEAL_KEY_1 through VAULT_UNSEAL_KEY_5

### 2. vault_shutdown.py
Gracefully shuts down the Vault server:
- Sends SIGTERM signal to the Vault process
- Cleans up the PID file
- Handles various edge cases (process not found, invalid PID)

Usage:
```bash
python3 setup/scripts/vault_shutdown.py
```

### 3. vault_start.py
Starts the Vault server and unseals it:
- Loads environment variables from .env.vault
- Starts the Vault server
- Automatically unseals using stored keys
- Verifies Vault is ready for connections

Usage:
```bash
python3 setup/scripts/vault_start.py
```

### 4. app_setup.py
Sets up the Flask application with Vault integration:
- Verifies Vault connection
- Creates necessary policies
- Generates application token
- Updates environment configuration

Usage:
```bash
python3 setup/scripts/app_setup.py [--token VAULT_TOKEN]
```

## Setup Process

1. Initial Setup:
   ```bash
   # Install required Python packages
   pip3 install requests python-dotenv

   # Run initial Vault setup
   python3 setup/scripts/vault_setup.py
   ```
   This will:
   - Install Vault
   - Initialize it
   - Create setup/.env.vault with credentials

2. For subsequent starts:
   ```bash
   python3 setup/scripts/vault_start.py
   ```
   This will:
   - Start Vault
   - Unseal it automatically
   - Verify it's ready

3. Setup the Flask application:
   ```bash
   python3 setup/scripts/app_setup.py
   ```
   This will:
   - Configure Vault policies
   - Create application token
   - Update .env file

4. To shut down Vault:
   ```bash
   python3 setup/scripts/vault_shutdown.py
   ```

## Environment Files

### setup/.env.vault
Contains Vault root credentials:
```
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=<root-token>
VAULT_UNSEAL_KEY_1=<key1>
VAULT_UNSEAL_KEY_2=<key2>
VAULT_UNSEAL_KEY_3=<key3>
VAULT_UNSEAL_KEY_4=<key4>
VAULT_UNSEAL_KEY_5=<key5>
```

### .env
Contains application configuration:
```
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=<app-token>
FLASK_APP=app.py
FLASK_ENV=production
```

## Security Notes

- All Vault communication is restricted to localhost
- TLS is disabled since we're only using localhost
- The UI is disabled for security
- Vault data persists between restarts in ~/.vault/data
- Environment files are created with 600 permissions (user read/write only)
- Application uses a limited-privilege token with specific policies

## Production Considerations

- Works with both development servers and production WSGI servers
- Vault token renewal is handled automatically by the application
- Vault data persists in the user's home directory (~/.vault)
- The application uses a limited-privilege token with specific policies
- Token TTL is set to 32 days by default (configurable in app_setup.py)

## Troubleshooting

1. If Vault fails to start:
   - Check if process is already running: `ps aux | grep vault`
   - Check vault.pid file exists and contains valid PID
   - Verify ~/.vault directory permissions

2. If Vault is sealed:
   - Run vault_start.py to automatically unseal
   - Verify setup/.env.vault contains valid unseal keys

3. If application can't connect to Vault:
   - Verify Vault is running: `curl http://127.0.0.1:8200/v1/sys/health`
   - Check .env contains valid VAULT_ADDR and VAULT_TOKEN
   - Verify token has correct policies using root token

## Directory Structure

```
setup/
├── documentation/
│   └── README.md
└── scripts/
    ├── vault_setup.py
    ├── vault_shutdown.py
    ├── vault_start.py
    └── app_setup.py
```

## Maintenance

- Monitor token expiration (32-day default)
- Regularly check Vault logs for issues
- Keep Vault version updated (modify version in vault_setup.py)
- Backup ~/.vault/data directory for persistence
