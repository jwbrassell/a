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
