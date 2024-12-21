#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
import subprocess
import shutil
from string import Template
import stat

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from utils.generate_dev_certs import setup_dev_certificates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directory(path, mode=0o700):
    """Set up directory with proper permissions."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        os.chmod(path, mode)
        return path
    except Exception as e:
        logger.error(f"Failed to set up directory {path}: {e}")
        raise

def create_vault_config(cert_paths, paths):
    """Create Vault configuration file from template."""
    try:
        template_path = project_root / "config" / "vault-secure.hcl.template"
        config_path = project_root / "config" / "vault-secure.hcl"
        
        with open(template_path, 'r') as f:
            template = Template(f.read())
        
        config = template.substitute(
            PATH_TO_SERVER_CERT=cert_paths['server_cert'],
            PATH_TO_SERVER_KEY=cert_paths['server_key'],
            PATH_TO_CA_CERT=cert_paths['ca_cert'],
            PATH_TO_VAULT_DATA=str(paths['data']),
            PATH_TO_AUDIT_LOG=str(paths['audit'] / 'audit.log'),
            PATH_TO_PLUGIN_DIR=str(paths['plugins'])
        )
        
        with open(config_path, 'w') as f:
            f.write(config)
        
        # Set proper permissions
        os.chmod(config_path, 0o600)
        
        return config_path
    except Exception as e:
        logger.error(f"Failed to create Vault configuration: {e}")
        raise

def setup_vault_directories():
    """Set up all required Vault directories with proper permissions."""
    try:
        paths = {
            'data': setup_directory(project_root / "vault-data"),
            'audit': setup_directory(project_root / "vault-audit"),
            'plugins': setup_directory(project_root / "vault-plugins"),
            'backup': setup_directory(project_root / "vault-backup"),
            'logs': setup_directory(project_root / "vault-logs")
        }
        
        # Create log files with proper permissions
        log_files = {
            'audit': paths['audit'] / 'audit.log',
            'error': paths['logs'] / 'error.log',
            'access': paths['logs'] / 'access.log'
        }
        
        for log_file in log_files.values():
            log_file.touch(mode=0o600)
        
        return paths
    except Exception as e:
        logger.error(f"Failed to set up Vault directories: {e}")
        raise

def create_env_file(cert_paths, config_path, paths):
    """Create environment file with Vault configuration."""
    try:
        env_path = project_root / ".env.vault"
        
        env_content = f"""# Vault Configuration
VAULT_ADDR=https://127.0.0.1:8200
VAULT_CACERT={cert_paths['ca_cert']}
VAULT_CLIENT_CERT={cert_paths['server_cert']}
VAULT_CLIENT_KEY={cert_paths['server_key']}
VAULT_CONFIG_PATH={config_path}
VAULT_LOG_LEVEL=info

# Directory Paths
VAULT_DATA_DIR={paths['data']}
VAULT_AUDIT_DIR={paths['audit']}
VAULT_PLUGIN_DIR={paths['plugins']}
VAULT_BACKUP_DIR={paths['backup']}
VAULT_LOG_DIR={paths['logs']}

# Security Settings
VAULT_DISABLE_MLOCK=true
VAULT_UI=false
VAULT_TLS_MIN_VERSION=tls13
VAULT_ENABLE_CLIENT_CERT_AUTH=true

# Monitoring Settings
VAULT_MONITOR_INTERVAL=300
VAULT_MONITOR_CERT_EXPIRY_THRESHOLD=30
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        # Set proper permissions
        os.chmod(env_path, 0o600)
        
        return env_path
    except Exception as e:
        logger.error(f"Failed to create environment file: {e}")
        raise

def verify_setup(cert_paths, config_path, env_path, paths):
    """Verify the setup is correct."""
    try:
        # Check file existence and permissions
        files_to_check = [
            (Path(cert_paths['ca_cert']), 0o600),
            (Path(cert_paths['server_cert']), 0o600),
            (Path(cert_paths['server_key']), 0o600),
            (Path(config_path), 0o600),
            (Path(env_path), 0o600)
        ]
        
        dirs_to_check = [
            (paths['data'], 0o700),
            (paths['audit'], 0o700),
            (paths['plugins'], 0o700),
            (paths['backup'], 0o700),
            (paths['logs'], 0o700)
        ]
        
        # Check files
        for file_path, expected_mode in files_to_check:
            if not file_path.exists():
                raise FileNotFoundError(f"Required file not found: {file_path}")
            
            stat_info = os.stat(file_path)
            actual_mode = stat.S_IMODE(stat_info.st_mode)
            if actual_mode != expected_mode:
                logger.warning(f"Incorrect permissions on {file_path}. Setting to {oct(expected_mode)}")
                os.chmod(file_path, expected_mode)
        
        # Check directories
        for dir_path, expected_mode in dirs_to_check:
            if not dir_path.exists():
                raise FileNotFoundError(f"Required directory not found: {dir_path}")
            
            stat_info = os.stat(dir_path)
            actual_mode = stat.S_IMODE(stat_info.st_mode)
            if actual_mode != expected_mode:
                logger.warning(f"Incorrect permissions on {dir_path}. Setting to {oct(expected_mode)}")
                os.chmod(dir_path, expected_mode)
        
        # Verify certificate validity
        verify_certificates(cert_paths)
        
        logger.info("Setup verification completed successfully")
        return True
    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        raise

def verify_certificates(cert_paths):
    """Verify SSL certificates are valid."""
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        
        for cert_type, path in cert_paths.items():
            if cert_type.endswith('_key'):
                continue  # Skip private keys
                
            with open(path, 'rb') as f:
                cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                
                # Check expiration
                from datetime import datetime
                if cert.not_valid_after < datetime.utcnow():
                    raise ValueError(f"Certificate has expired: {path}")
                
                # Log certificate info
                logger.info(f"Certificate {cert_type} is valid until: {cert.not_valid_after}")
    except Exception as e:
        logger.error(f"Certificate verification failed: {e}")
        raise

def setup_monitoring():
    """Set up security monitoring cron job."""
    try:
        monitor_script = project_root / "utils" / "vault_security_monitor.py"
        cron_command = f"*/5 * * * * {sys.executable} {monitor_script} >> {project_root}/vault-logs/monitor.log 2>&1"
        
        # Add to crontab if not already present
        current_crontab = subprocess.getoutput("crontab -l")
        if str(monitor_script) not in current_crontab:
            with open("/tmp/vault_crontab", "w") as f:
                if current_crontab and "no crontab" not in current_crontab:
                    f.write(current_crontab + "\n")
                f.write(cron_command + "\n")
            
            subprocess.run(["crontab", "/tmp/vault_crontab"], check=True)
            os.remove("/tmp/vault_crontab")
            
        logger.info("Security monitoring cron job configured")
    except Exception as e:
        logger.error(f"Failed to set up monitoring: {e}")
        logger.info("Please manually add the following to your crontab:")
        logger.info(cron_command)

def main():
    """Main setup function."""
    try:
        logger.info("Starting secure Vault setup...")
        
        # Generate certificates
        logger.info("Generating SSL certificates...")
        cert_paths = setup_dev_certificates()
        
        # Set up Vault directories
        logger.info("Setting up Vault directories...")
        paths = setup_vault_directories()
        
        # Create Vault configuration
        logger.info("Creating Vault configuration...")
        config_path = create_vault_config(cert_paths, paths)
        
        # Create environment file
        logger.info("Creating environment file...")
        env_path = create_env_file(cert_paths, config_path, paths)
        
        # Set up monitoring
        logger.info("Setting up security monitoring...")
        setup_monitoring()
        
        # Verify setup
        logger.info("Verifying setup...")
        verify_setup(cert_paths, config_path, env_path, paths)
        
        logger.info(f"""
Secure Vault setup completed successfully!

Configuration files created:
1. SSL Certificates in ./certs/
2. Vault Config: {config_path}
3. Environment File: {env_path}

Directories created:
1. Data: {paths['data']}
2. Audit Logs: {paths['audit']}
3. Plugins: {paths['plugins']}
4. Backups: {paths['backup']}
5. Logs: {paths['logs']}

Security monitoring is configured to run every 5 minutes.

To start Vault with the secure configuration:
1. Source the environment file:
   source {env_path}

2. Start Vault:
   vault server -config={config_path}

3. Initialize Vault (first time only):
   export VAULT_ADDR=https://127.0.0.1:8200
   vault operator init

4. Unseal Vault:
   vault operator unseal

Remember to:
- Securely store the unseal keys and root token
- Monitor the audit logs in {paths['audit']}
- Check security monitoring logs in {paths['logs']}/monitor.log
- Regularly rotate certificates and credentials
- Keep backups in {paths['backup']}
""")
        
    except Exception as e:
        logger.error(f"Failed to set up secure Vault: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
