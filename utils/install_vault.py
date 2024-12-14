#!/usr/bin/env python3
"""
Vault Installation Script
Supports:
- macOS (Intel/ARM) via Homebrew
- Ubuntu via apt
- Rocky Linux via dnf
- Windows 10/11 via direct download
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultInstaller:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.bin_dir = self.base_dir / "bin"
        
    def _is_macos(self):
        return platform.system().lower() == 'darwin'
        
    def _is_windows(self):
        return platform.system().lower() == 'windows'
        
    def _is_linux(self):
        return platform.system().lower() == 'linux'
        
    def _get_linux_distro(self):
        """Get Linux distribution name."""
        try:
            with open('/etc/os-release') as f:
                lines = f.readlines()
                info = dict(line.strip().split('=', 1) for line in lines if '=' in line)
                return info.get('ID', '').strip('"').lower()
        except FileNotFoundError:
            return None
            
    def _install_macos(self):
        """Install Vault via Homebrew on macOS."""
        try:
            # Check if Homebrew is installed
            subprocess.run(['brew', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("""
Homebrew is required but not installed. Install it with:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
""")
            sys.exit(1)
            
        try:
            # Install Vault
            logger.info("Installing Vault via Homebrew...")
            subprocess.run(['brew', 'install', 'vault'], check=True)
            
            # Create symlink in project's bin directory
            self.bin_dir.mkdir(exist_ok=True)
            vault_path = Path('/opt/homebrew/bin/vault')
            if not vault_path.exists():
                vault_path = Path('/usr/local/bin/vault')  # Intel Mac path
                
            if not vault_path.exists():
                raise FileNotFoundError("Could not find Vault binary")
                
            symlink_path = self.bin_dir / 'vault'
            if symlink_path.exists():
                symlink_path.unlink()
            symlink_path.symlink_to(vault_path)
            
            logger.info("Vault installed successfully via Homebrew")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Vault: {e}")
            raise
            
    def _install_ubuntu(self):
        """Install Vault on Ubuntu."""
        try:
            logger.info("Adding HashiCorp GPG key and repository...")
            
            # Add HashiCorp GPG key
            subprocess.run([
                'sudo', 'apt-get', 'update'
            ], check=True)
            
            subprocess.run([
                'sudo', 'apt-get', 'install', '-y', 'gpg'
            ], check=True)
            
            subprocess.run([
                'wget', '-O-', 'https://apt.releases.hashicorp.com/gpg',
                '|', 'sudo', 'gpg', '--dearmor', '-o', '/usr/share/keyrings/hashicorp-archive-keyring.gpg'
            ], check=True, shell=True)
            
            # Add HashiCorp repository
            subprocess.run([
                'echo', 'deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main',
                '|', 'sudo', 'tee', '/etc/apt/sources.list.d/hashicorp.list'
            ], check=True, shell=True)
            
            # Install Vault
            logger.info("Installing Vault...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'vault'], check=True)
            
            # Create symlink in project's bin directory
            self.bin_dir.mkdir(exist_ok=True)
            vault_path = Path('/usr/bin/vault')
            symlink_path = self.bin_dir / 'vault'
            if symlink_path.exists():
                symlink_path.unlink()
            symlink_path.symlink_to(vault_path)
            
            logger.info("Vault installed successfully on Ubuntu")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Vault: {e}")
            raise
            
    def _install_rocky(self):
        """Install Vault on Rocky Linux."""
        try:
            logger.info("Adding HashiCorp repository...")
            
            # Add HashiCorp repository
            subprocess.run([
                'sudo', 'yum', 'install', '-y', 'yum-utils'
            ], check=True)
            
            subprocess.run([
                'sudo', 'yum-config-manager', '--add-repo',
                'https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo'
            ], check=True)
            
            # Install Vault
            logger.info("Installing Vault...")
            subprocess.run(['sudo', 'yum', '-y', 'install', 'vault'], check=True)
            
            # Create symlink in project's bin directory
            self.bin_dir.mkdir(exist_ok=True)
            vault_path = Path('/usr/bin/vault')
            symlink_path = self.bin_dir / 'vault'
            if symlink_path.exists():
                symlink_path.unlink()
            symlink_path.symlink_to(vault_path)
            
            logger.info("Vault installed successfully on Rocky Linux")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Vault: {e}")
            raise
            
    def _install_windows(self):
        """Install Vault on Windows."""
        try:
            import requests
            import zipfile
            
            logger.info("Downloading Vault for Windows...")
            
            # Create directories
            self.bin_dir.mkdir(exist_ok=True)
            downloads_dir = self.base_dir / "downloads"
            downloads_dir.mkdir(exist_ok=True)
            
            # Download Vault
            url = "https://releases.hashicorp.com/vault/1.15.2/vault_1.15.2_windows_amd64.zip"
            zip_path = downloads_dir / "vault.zip"
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Extract Vault
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.bin_dir)
                
            # Clean up
            zip_path.unlink()
            downloads_dir.rmdir()
            
            logger.info("Vault installed successfully on Windows")
            
        except Exception as e:
            logger.error(f"Failed to install Vault: {e}")
            raise
            
    def install(self):
        """Install Vault for the current platform."""
        try:
            if self._is_macos():
                self._install_macos()
            elif self._is_windows():
                self._install_windows()
            elif self._is_linux():
                distro = self._get_linux_distro()
                if distro == 'ubuntu':
                    self._install_ubuntu()
                elif distro == 'rocky':
                    self._install_rocky()
                else:
                    raise ValueError(f"Unsupported Linux distribution: {distro}")
            else:
                raise ValueError(f"Unsupported platform: {platform.system()}")
                
            logger.info(f"""
Vault installation complete!

The Vault binary is available at: {self.bin_dir / 'vault'}

To verify the installation:
{self.bin_dir / 'vault'} version
""")
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    installer = VaultInstaller()
    installer.install()
