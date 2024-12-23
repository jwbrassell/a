#!/usr/bin/env python3
"""
Vault Installer Script
Downloads and installs HashiCorp Vault
"""

import os
import sys
import platform
import requests
import subprocess
import logging
import shutil
import tempfile
from pathlib import Path
import zipfile
import stat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultInstaller:
    VAULT_VERSION = "1.13.3"  # Latest stable version
    DOWNLOAD_BASE_URL = "https://releases.hashicorp.com/vault"

    def __init__(self):
        self.base_dir = Path.cwd()
        self.bin_dir = self.base_dir / "bin"
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()

    def get_download_url(self):
        """Get the appropriate Vault download URL for the current system."""
        if self.system == "darwin":
            if self.machine == "arm64":
                arch = "arm64"
            else:
                arch = "amd64"
            os_name = "darwin"
        elif self.system == "linux":
            if self.machine == "aarch64":
                arch = "arm64"
            elif "arm" in self.machine:
                arch = "arm"
            else:
                arch = "amd64"
            os_name = "linux"
        elif self.system == "windows":
            arch = "amd64"
            os_name = "windows"
        else:
            raise Exception(f"Unsupported system: {self.system}")

        filename = f"vault_{self.VAULT_VERSION}_{os_name}_{arch}.zip"
        return f"{self.DOWNLOAD_BASE_URL}/{self.VAULT_VERSION}/{filename}"

    def download_vault(self):
        """Download Vault binary."""
        url = self.get_download_url()
        logger.info(f"Downloading Vault from {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "vault.zip"
            
            # Download zip file
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Create bin directory if it doesn't exist
            self.bin_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract vault binary
            with zipfile.ZipFile(zip_path) as zip_ref:
                zip_ref.extractall(self.bin_dir)
            
            # Make vault binary executable
            vault_binary = self.bin_dir / "vault"
            if self.system == "windows":
                vault_binary = self.bin_dir / "vault.exe"
            
            vault_binary.chmod(vault_binary.stat().st_mode | stat.S_IEXEC)
            logger.info(f"Vault binary installed at {vault_binary}")

    def verify_installation(self):
        """Verify Vault installation."""
        try:
            vault_path = self.bin_dir / "vault"
            if self.system == "windows":
                vault_path = self.bin_dir / "vault.exe"

            result = subprocess.run(
                [str(vault_path), 'version'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Vault installation verified: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Vault verification failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error verifying Vault installation: {e}")
            return False

    def install(self):
        """Install Vault."""
        try:
            logger.info("Starting Vault installation...")
            
            # Check if Vault is already installed
            if (self.bin_dir / "vault").exists() or (self.bin_dir / "vault.exe").exists():
                logger.info("Vault is already installed")
                if self.verify_installation():
                    return True
                logger.info("Existing installation may be corrupted, reinstalling...")
            
            # Download and install Vault
            self.download_vault()
            
            # Verify installation
            if not self.verify_installation():
                raise Exception("Vault installation verification failed")
            
            logger.info("Vault installation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install Vault: {e}")
            raise

if __name__ == "__main__":
    installer = VaultInstaller()
    installer.install()
