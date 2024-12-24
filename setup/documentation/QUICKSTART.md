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

Linux-specific:
- If you see "permission denied", the script will automatically fall back to using disable_mlock
- Make sure the vault binary is executable:
  ```bash
  chmod +x ~/.vault/vault
  ```
- If the process starts but immediately stops:
  ```bash
  # Check the logs
  tail -f vault.log
  
  # Verify the process is running in its own group
  ps -ef | grep vault
  
  # Check if port 8200 is already in use
  sudo lsof -i :8200
  
  # Kill any existing vault processes
  pkill vault
  
  # Clean up and try again
  rm -f vault.pid nohup.out vault.log
  python3 setup/scripts/vault_setup.py
  ```

General issues:
- If Vault seems to start but commands don't work:
  ```bash
  # Ensure VAULT_ADDR is set
  export VAULT_ADDR='http://127.0.0.1:8200'
  
  # Check process status
  ps aux | grep vault
  
  # Check logs
  tail -f vault.log
  ```

- If process exists but Vault isn't responding:
  ```bash
  # Full cleanup and restart
  python3 setup/scripts/vault_shutdown.py
  rm -f vault.pid vault.log
  rm -rf ~/.vault/data/*  # Clear vault data if needed
  python3 setup/scripts/vault_setup.py  # Complete fresh start
  ```

- For detailed debugging:
  ```bash
  # Check all vault-related processes and their process groups
  ps -ef | grep vault
  
  # Check listening ports
  sudo lsof -i :8200
  
  # Check system logs (Linux)
  sudo journalctl | grep vault
  
  # Check file permissions
  ls -la ~/.vault/
  ls -la vault.pid vault.log
  
  # Verify environment
  echo $VAULT_ADDR
  echo $PATH | grep vault
  ```
