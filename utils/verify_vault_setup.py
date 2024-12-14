#!/usr/bin/env python3
"""
Vault Setup Verification Script
Checks the Vault installation and configuration for common issues
"""

import os
import sys
import ssl
import socket
import logging
import subprocess
import requests
import platform
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultVerifier:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.bin_dir = self.base_dir / "bin"
        self.cert_dir = self.base_dir / "instance" / "certs"
        self.config_dir = self.base_dir / "config"
        self.vault_data_dir = self.base_dir / "vault-data"
        self.logs_dir = self.base_dir / "logs"
        
        # Required files
        self.required_files = {
            'vault_binary': self.bin_dir / "vault",
            'dev_config': self.config_dir / "vault-dev.hcl",
            'server_cert': self.cert_dir / "server.crt",
            'server_key': self.cert_dir / "server.key"
        }
        
        # Environment variables
        self.required_env = ['VAULT_ADDR', 'VAULT_TOKEN']
        
        # Platform-specific settings
        self.is_windows = platform.system().lower() == 'windows'
        if self.is_windows:
            self.required_files['vault_binary'] = self.bin_dir / "vault.exe"

    def check_files(self):
        """Check if all required files exist."""
        logger.info("Checking required files...")
        missing_files = []
        
        for name, path in self.required_files.items():
            if not path.exists():
                missing_files.append(name)
                logger.error(f"Missing {name}: {path}")
            else:
                logger.info(f"Found {name}: {path}")
                
        return len(missing_files) == 0

    def check_permissions(self):
        """Check file permissions."""
        logger.info("Checking file permissions...")
        if self.is_windows:
            logger.info("Skipping permission checks on Windows")
            return True
            
        try:
            # Check certificate permissions
            cert_perms = oct(self.required_files['server_cert'].stat().st_mode)[-3:]
            key_perms = oct(self.required_files['server_key'].stat().st_mode)[-3:]
            
            if cert_perms != '644':
                logger.error(f"Invalid certificate permissions: {cert_perms}, should be 644")
                return False
                
            if key_perms != '600':
                logger.error(f"Invalid key permissions: {key_perms}, should be 600")
                return False
                
            # Check data directory permissions
            if self.vault_data_dir.exists():
                data_perms = oct(self.vault_data_dir.stat().st_mode)[-3:]
                if data_perms != '750':
                    logger.error(f"Invalid data directory permissions: {data_perms}, should be 750")
                    return False
                    
            logger.info("File permissions are correct")
            return True
            
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            return False

    def check_environment(self):
        """Check environment variables."""
        logger.info("Checking environment variables...")
        missing_env = []
        
        for var in self.required_env:
            if not os.getenv(var):
                missing_env.append(var)
                logger.error(f"Missing environment variable: {var}")
            else:
                logger.info(f"Found environment variable: {var}")
                
        return len(missing_env) == 0

    def check_vault_version(self):
        """Check Vault version."""
        logger.info("Checking Vault version...")
        try:
            result = subprocess.run(
                [str(self.required_files['vault_binary']), 'version'],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip()
            logger.info(f"Vault version: {version}")
            return True
        except Exception as e:
            logger.error(f"Error checking Vault version: {e}")
            return False

    def check_ssl_certificates(self):
        """Check SSL certificate validity."""
        logger.info("Checking SSL certificates...")
        try:
            cert_path = self.required_files['server_cert']
            key_path = self.required_files['server_key']
            
            # Check certificate expiration
            with open(cert_path) as f:
                cert_data = ssl.PEM_cert_to_DER_cert(f.read())
                cert = ssl.DER_cert_to_PEM_cert(cert_data)
                x509 = ssl.PEM_cert_to_DER_cert(cert)
                
            # Get certificate expiration
            context = ssl.create_default_context()
            context.load_verify_locations(cafile=str(cert_path))
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                with context.wrap_socket(sock, server_hostname='localhost') as ssock:
                    cert = ssock.getpeercert()
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_remaining = (not_after - datetime.now()).days
                    
                    if days_remaining < 30:
                        logger.warning(f"Certificate expires in {days_remaining} days")
                    else:
                        logger.info(f"Certificate valid for {days_remaining} days")
                        
            logger.info("SSL certificates are valid")
            return True
            
        except Exception as e:
            logger.error(f"Error checking SSL certificates: {e}")
            return False

    def check_vault_connection(self):
        """Check connection to Vault server."""
        logger.info("Checking Vault connection...")
        try:
            vault_addr = os.getenv('VAULT_ADDR')
            if not vault_addr:
                logger.error("VAULT_ADDR not set")
                return False
                
            # Parse URL
            parsed_url = urlparse(vault_addr)
            if parsed_url.scheme != 'https':
                logger.error("Vault address must use HTTPS")
                return False
                
            if parsed_url.hostname not in ['localhost', '127.0.0.1']:
                logger.error("Vault address must be localhost")
                return False
                
            # Try connection
            response = requests.get(
                f"{vault_addr}/v1/sys/health",
                verify=False if os.getenv('FLASK_ENV') == 'development' else True
            )
            
            if response.status_code == 200:
                logger.info("Successfully connected to Vault")
                return True
            else:
                logger.error(f"Failed to connect to Vault: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Vault: {e}")
            return False

    def verify(self):
        """Run all verification checks."""
        checks = [
            self.check_files(),
            self.check_permissions(),
            self.check_environment(),
            self.check_vault_version(),
            self.check_ssl_certificates(),
            self.check_vault_connection()
        ]
        
        success = all(checks)
        
        if success:
            logger.info("All verification checks passed!")
        else:
            logger.error("Some verification checks failed!")
            
        return success

def main():
    verifier = VaultVerifier()
    success = verifier.verify()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
