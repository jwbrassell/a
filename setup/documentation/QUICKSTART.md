# Quick Start Guide

## First Time Setup

1. Clone and setup Python environment:
```bash
git clone [repository-url]
cd [repository-name]

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Setup Vault and Flask integration:
```bash
# Install and initialize Vault
python3 setup/scripts/vault_setup.py

# Configure Flask app integration with Vault
python3 setup/scripts/app_setup.py
```

## Running the App

### Development Mode
```bash
# 1. Start Vault (if not running)
python3 setup/scripts/vault_start.py

# 2. Run Flask development server
flask run
```

### Production Mode
```bash
# 1. Start Vault (if not running)
python3 setup/scripts/vault_start.py

# 2. Run with Gunicorn
gunicorn wsgi:app
```

## Stopping Everything
```bash
# Stop Flask/Gunicorn (Ctrl+C)

# Shutdown Vault
python3 setup/scripts/vault_shutdown.py
```

## File Locations

- Vault data: ~/.vault/data
- Vault credentials: setup/.env.vault
- App configuration: .env

## Notes

- Everything runs on localhost only
- No SSL/TLS (not needed for localhost)
- No Vault UI (disabled for security)
- Vault must be running before starting Flask/Gunicorn

## Troubleshooting

If Vault fails to start:

1. Check the logs:
```bash
cat vault.log
```

2. Verify permissions:
```bash
# Linux
ls -l ~/.vault/vault
ls -l ~/.vault/config.hcl

# Should show:
# -rwxr-xr-x for vault binary
# -rw------- for config.hcl
```

3. Verify Vault is running:
```bash
curl http://127.0.0.1:8200/v1/sys/health
```

4. Common issues:
- On Linux, if you see "permission denied", the script will automatically fall back to using disable_mlock
- If Vault seems to start but commands don't work, ensure VAULT_ADDR is set:
  ```bash
  export VAULT_ADDR='http://127.0.0.1:8200'
  ```
- If you see "Error checking seal status", wait a few seconds and try again
- If process exists but Vault isn't responding, try:
  ```bash
  # Stop Vault
  python3 setup/scripts/vault_shutdown.py
  
  # Remove any leftover files
  rm vault.pid vault.log
  
  # Start fresh
  python3 setup/scripts/vault_start.py
  ```
