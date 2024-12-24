#!/usr/bin/env python3
import os
import sys
import json
import platform
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple

class VaultSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.is_linux = self.system == "linux"
        self.is_mac = self.system == "darwin"
        self.vault_version = "1.13.3"  # Update as needed
        self.vault_dir = Path.home() / ".vault"
        self.vault_bin = self.vault_dir / "vault"
        self.vault_config = self.vault_dir / "config.hcl"
        self.vault_data = self.vault_dir / "data"
        self.env_file = Path("setup/.env.vault")
        self.pid_file = Path("vault.pid")

    def check_prerequisites(self) -> None:
        """Check and install required system packages."""
        try:
            if self.is_linux:
                # Check if we're on CentOS/Rocky
                with open("/etc/os-release") as f:
                    os_info = f.read().lower()
                    is_centos = "centos" in os_info
                    is_rocky = "rocky" in os_info
                
                if not (is_centos or is_rocky):
                    raise Exception("This script currently supports CentOS/Rocky Linux distributions")
                
                # Install required packages
                subprocess.run(["sudo", "yum", "install", "-y", "wget", "unzip"], check=True)
            
            elif self.is_mac:
                # Check if brew is installed
                if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
                    raise Exception("Homebrew is required for Mac installation. Visit https://brew.sh")
            else:
                raise Exception(f"Unsupported operating system: {self.system}")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install prerequisites: {str(e)}")

    def download_and_install_vault(self) -> None:
        """Download and install Vault binary."""
        try:
            self.vault_dir.mkdir(parents=True, exist_ok=True)
            self.vault_data.mkdir(parents=True, exist_ok=True)

            if self.is_linux:
                url = f"https://releases.hashicorp.com/vault/{self.vault_version}/vault_{self.vault_version}_linux_amd64.zip"
                subprocess.run(["wget", "-O", "vault.zip", url], check=True)
                subprocess.run(["unzip", "vault.zip"], check=True)
                subprocess.run(["mv", "vault", str(self.vault_bin)], check=True)
                subprocess.run(["rm", "vault.zip"], check=True)
                subprocess.run(["sudo", "setcap", "cap_ipc_lock=+ep", str(self.vault_bin)], check=True)
            
            elif self.is_mac:
                subprocess.run(["brew", "install", "vault"], check=True)
                # Create symlink to our vault directory
                subprocess.run(["ln", "-sf", "/usr/local/bin/vault", str(self.vault_bin)], check=True)

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install Vault: {str(e)}")

    def create_config(self) -> None:
        """Create Vault configuration file."""
        config = f"""
storage "file" {{
    path = "{self.vault_data}"
}}

listener "tcp" {{
    address = "127.0.0.1:8200"
    tls_disable = 1
}}

api_addr = "http://127.0.0.1:8200"
disable_mlock = true
ui = false
        """
        self.vault_config.write_text(config.strip())

    def start_vault(self) -> None:
        """Start Vault server."""
        try:
            # Start vault server
            process = subprocess.Popen(
                [str(self.vault_bin), "server", "-config", str(self.vault_config)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # This creates a new process group
            )
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            
            # Wait for Vault to start
            time.sleep(2)
            
            # Set environment variable
            os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
            
            # Check if Vault is running
            for _ in range(5):  # Try 5 times
                try:
                    requests.get("http://127.0.0.1:8200/v1/sys/health")
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(2)
            else:
                raise Exception("Vault failed to start")

        except Exception as e:
            raise Exception(f"Failed to start Vault: {str(e)}")

    def initialize_vault(self) -> Tuple[List[str], str]:
        """Initialize Vault and return unseal keys and root token."""
        try:
            # Initialize vault
            init_response = requests.put(
                "http://127.0.0.1:8200/v1/sys/init",
                json={"secret_shares": 5, "secret_threshold": 3}
            ).json()

            return init_response["keys"], init_response["root_token"]

        except Exception as e:
            raise Exception(f"Failed to initialize Vault: {str(e)}")

    def save_credentials(self, keys: List[str], token: str) -> None:
        """Save unseal keys and token to .env file."""
        env_content = f"""
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN={token}
VAULT_UNSEAL_KEY_1={keys[0]}
VAULT_UNSEAL_KEY_2={keys[1]}
VAULT_UNSEAL_KEY_3={keys[2]}
VAULT_UNSEAL_KEY_4={keys[3]}
VAULT_UNSEAL_KEY_5={keys[4]}
        """.strip()
        
        self.env_file.write_text(env_content)
        # Secure the file
        self.env_file.chmod(0o600)

    def setup(self) -> None:
        """Run the complete setup process."""
        print("Starting Vault setup...")
        
        print("Checking prerequisites...")
        self.check_prerequisites()
        
        print("Installing Vault...")
        self.download_and_install_vault()
        
        print("Creating configuration...")
        self.create_config()
        
        print("Starting Vault server...")
        self.start_vault()
        
        print("Initializing Vault...")
        keys, token = self.initialize_vault()
        
        print("Saving credentials...")
        self.save_credentials(keys, token)
        
        print(f"""
Vault setup complete!
- Vault is running on http://127.0.0.1:8200
- Credentials saved to {self.env_file}
- PID saved to {self.pid_file}
        """.strip())

if __name__ == "__main__":
    try:
        setup = VaultSetup()
        setup.setup()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
