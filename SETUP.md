# Verified Setup Process

This document outlines the step-by-step process to set up the vault integration application with all necessary components.

## Prerequisites

- Python 3.x installed
- Vault binary (will be automatically installed if needed)

## Setup Steps

### 1. Vault Setup

There are two options for setting up Vault:

#### Option A: Development Setup (Recommended for local development)
```bash
python setup/setup_dev_vault.py
```
This script will:
- Install Vault if not present
- Clean existing Vault data
- Generate SSL certificates automatically
- Initialize Vault with development configuration
- Mount KVv2 secrets engine
- Save credentials to `.env.vault`
- Update `.env` with Vault configuration

#### Option B: Production Setup
```bash
python setup.py
```
This script will:
- Install Vault if needed
- Generate self-signed SSL certificates automatically
- Configure Vault with HTTPS enabled
- Initialize and unseal Vault
- Save credentials and certificates to:
  - `instance/certs/` (SSL certificates)
  - `.env.vault` (Vault credentials)
  - `.env` (Environment configuration)

### 2. SSL Certificates

The system now handles SSL certificates automatically:

#### Development Environment
- Self-signed certificates are generated automatically
- Stored in `instance/certs/` with secure permissions (600)
- Certificate paths are configured automatically
- No manual intervention required

#### Production Environment
- Self-signed certificates are generated automatically
- Stored securely in `instance/certs/`:
  - `vault-ca.pem`: Certificate
  - `vault-ca-key.pem`: Private key
- Proper permissions (600) are set automatically
- HTTPS is enforced in production

To recreate certificates:
```bash
# Remove existing certificates
rm -rf instance/certs/

# Run setup again
python setup.py
```

### 3. Application Setup

There are two ways to complete the application setup:

#### Option A: Using the Environment Setup Script (Recommended)
```bash
./setup/setup_environment.sh
```
This script will:
- Create necessary directories (vault-data, vault-plugins, logs, instance)
- Start and initialize Vault with HTTPS enabled
- Initialize the database
- Run the complete application setup
- Perform deployment verification if available

#### Option B: Manual Setup Steps
```bash
# 1. Initialize the database with migrations
flask db upgrade

# 2. Initialize project configurations
python setup/init_project_config.py
# This sets up:
# - Default project statuses (Not Started, Planning, Active, etc.)
# - Default project priorities (Low, Medium, High, Critical)

# 3. Complete the application setup
python setup/setup_complete.py
```

This script will:
1. Initialize all blueprint permissions including:
   - AWS Manager permissions
   - Database Reports permissions
   - OnCall permissions
   - Projects permissions
   - Core app permissions
2. Create admin role with full permissions
3. Create admin user account
4. Verify the complete setup

## Starting the Application

After setup is complete, start the Flask application:

### Development
```bash
flask run
```

### Production
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

## Default Admin Credentials

After setup is complete, you can log in with:
- Username: `admin`
- Password: `admin`

**Important:** Change the admin password after first login.

## Verification

To verify everything is working:

1. Check Vault status and HTTPS configuration:
```bash
# Check Vault status
vault status

# Verify HTTPS is enabled (Production only)
curl -k https://127.0.0.1:8201/v1/sys/health
```

2. Verify you can log in to the application using the admin credentials

3. Confirm access to all features:
   - AWS Manager
   - Database Reports
   - OnCall System
   - Projects
   - Admin Panel

## Troubleshooting

If you encounter issues:

1. Check the logs:
   - Vault logs: `logs/vault.log`
   - Application logs will be in the standard output
   - Certificate generation logs in setup output

2. Verify environment files:
   - `.env.vault` contains Vault credentials
   - `.env` contains updated Vault configuration
   - Check certificate paths in `instance/certs/`

3. SSL Certificate Issues:
   ```bash
   # Verify certificate permissions
   ls -l instance/certs/
   
   # Verify certificate validity
   openssl x509 -in instance/certs/vault-ca.pem -text -noout
   ```

4. If needed, you can clean and restart:
   ```bash
   # Stop any running Vault instance
   pkill vault  # On Unix/Linux
   # OR
   taskkill /F /IM vault.exe  # On Windows
   
   # Remove existing data and certificates
   rm -rf vault-data/
   rm -rf instance/certs/
   rm .env.vault
   
   # Start fresh setup
   python setup.py
   ```

## Security Notes

1. The default admin password should be changed immediately after setup
2. The development setup is not suitable for production use
3. Vault credentials in `.env.vault` should be secured appropriately
4. SSL certificates in `instance/certs/` are crucial for security:
   - Keep private keys secure
   - Ensure proper permissions (600)
   - In production, consider using trusted CA certificates instead of self-signed
5. HTTPS is enforced in production for secure communication
6. For production deployment, use `config/vault-prod.hcl.template` instead of the development configuration
