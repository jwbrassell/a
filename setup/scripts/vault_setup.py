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
        self.vault_config = self.vault_dir / "config/vault.hcl"
        self.vault_data = self.vault_dir / "data"
        self.env_file = Path.home() / ".env.vault"
        self.pid_file = Path("vault.pid")

    def check_prerequisites(self) -> None:
        """Check and install required system packages."""
        try:
            if self.is_linux:
                # Check Linux distribution
                with open("/etc/os-release") as f:
                    os_info = f.read().lower()
                    is_centos = "centos" in os_info
                    is_rocky = "rocky" in os_info
                    is_amazon = "amazon linux" in os_info
                
                if not (is_centos or is_rocky or is_amazon):
                    raise Exception("This script supports CentOS, Rocky Linux, and Amazon Linux distributions")
                
                # Install required packages
                subprocess.run(["sudo", "yum", "install", "-y", "wget", "unzip", "python3-pip", "net-tools"], check=True)
                subprocess.run(["pip3", "install", "--user", "requests"], check=True)
            
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
            # Create directories with proper permissions
            for directory in [self.vault_dir, self.vault_data, self.vault_config.parent]:
                directory.mkdir(parents=True, exist_ok=True)
                directory.chmod(0o700)  # Secure the directories
                if self.is_linux:
                    # Ensure proper ownership
                    subprocess.run(["sudo", "chown", "-R", "ec2-user:ec2-user", str(directory)], check=True)

            if self.is_linux:
                # Download and extract Vault
                url = f"https://releases.hashicorp.com/vault/{self.vault_version}/vault_{self.vault_version}_linux_amd64.zip"
                subprocess.run(["wget", "-O", "vault.zip", url], check=True)
                subprocess.run(["unzip", "-o", "vault.zip"], check=True)  # -o to overwrite
                subprocess.run(["mv", "-f", "vault", str(self.vault_bin)], check=True)
                subprocess.run(["rm", "vault.zip"], check=True)
                
                # Set proper permissions
                self.vault_bin.chmod(0o755)  # Executable permissions
                
                try:
                    # Try setting capabilities (requires sudo)
                    subprocess.run(["sudo", "setcap", "cap_ipc_lock=+ep", str(self.vault_bin)], check=True)
                except subprocess.CalledProcessError:
                    print("Warning: Could not set IPC_LOCK capability. Using disable_mlock=true instead.")
                
                # Ensure vault binary is accessible
                os.environ["PATH"] = f"{self.vault_dir}:{os.environ['PATH']}"
                os.environ["HOME"] = "/home/ec2-user"  # Ensure HOME is set correctly
            
            elif self.is_mac:
                subprocess.run(["brew", "install", "vault"], check=True)
                # Create symlink to our vault directory
                subprocess.run(["ln", "-sf", "/usr/local/bin/vault", str(self.vault_bin)], check=True)

            # Verify installation
            try:
                subprocess.run([str(self.vault_bin), "version"], check=True)
            except subprocess.CalledProcessError:
                raise Exception("Vault binary installed but not executable. Check permissions.")

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install Vault: {str(e)}")

    def create_config(self) -> None:
        """Create Vault configuration file."""
        # Always use disable_mlock for our localhost setup
        config = f"""
storage "file" {{
    path = "/home/ec2-user/.vault/data"
}}

listener "tcp" {{
    address = "127.0.0.1:8200"
    tls_disable = 1
}}

api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"
disable_mlock = true
ui = false
        """
        self.vault_config.write_text(config.strip())
        self.vault_config.chmod(0o600)  # Secure the config file

    def start_vault(self) -> None:
        """Start Vault server."""
        try:
            # Set environment variable
            os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
            
            # Check if Vault is already running and accessible
            try:
                subprocess.run([str(self.vault_bin), "status"], check=True)
                print("Existing Vault is accessible, using it")
                return
            except subprocess.CalledProcessError:
                pass
            
            # Kill any existing Vault process
            try:
                subprocess.run(["sudo", "pkill", "-f", "vault server"], check=False)
                time.sleep(2)
            except subprocess.CalledProcessError:
                pass
            
            # Clean up any existing files
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            # Start Vault
            print("Starting Vault...")
            log_file = Path("vault.log")
            process = subprocess.Popen(
                [str(self.vault_bin), "server", "-config", str(self.vault_config)],
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            self.pid_file.chmod(0o600)
            
            # Wait for Vault to start
            print("Waiting for Vault to start...")
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get("http://127.0.0.1:8200/v1/sys/health")
                    if response.status_code in (200, 429, 472, 473):
                        print("Vault is running!")
                        time.sleep(2)  # Give it a moment to fully initialize
                        break
                except requests.exceptions.ConnectionError:
                    if attempt == max_attempts - 1:
                        if log_file.exists():
                            print(f"Vault log contents:\n{log_file.read_text()}")
                        raise Exception("Vault failed to start. Check vault.log for details.")
                    print(f"Waiting for Vault to start (attempt {attempt + 1}/{max_attempts})...")
                    time.sleep(1)

        except Exception as e:
            # Clean up PID file if startup failed
            if self.pid_file.exists():
                self.pid_file.unlink()
            raise Exception(f"Failed to start Vault: {str(e)}")

    def initialize_vault(self) -> Tuple[List[str], str]:
        """Initialize Vault and return unseal keys and root token."""
        try:
            # Check if vault is already initialized
            init_status = requests.get("http://127.0.0.1:8200/v1/sys/init")
            if init_status.json().get("initialized", False):
                print("Vault is already initialized")
                
                # Check if vault is sealed
                seal_status = requests.get("http://127.0.0.1:8200/v1/sys/seal-status")
                if seal_status.json().get("sealed", True):
                    print("Vault is sealed, attempting to unseal with existing keys...")
                    if self.env_file.exists():
                        # Parse existing keys from env file
                        env_content = self.env_file.read_text()
                        keys = []
                        for line in env_content.splitlines():
                            if line.startswith("VAULT_UNSEAL_KEY_"):
                                keys.append(line.split("=")[1].strip())
                        
                        # Use first 3 keys to unseal
                        if len(keys) >= 3:
                            for key in keys[:3]:
                                unseal_response = requests.put(
                                    "http://127.0.0.1:8200/v1/sys/unseal",
                                    json={"key": key}
                                ).json()
                                print(f"Unseal progress: {unseal_response.get('progress', 0)}/3")
                            
                            # Verify unseal was successful
                            time.sleep(2)
                            seal_status = requests.get("http://127.0.0.1:8200/v1/sys/seal-status").json()
                            if not seal_status.get("sealed", True):
                                print("Vault unsealed successfully")
                            else:
                                print("Warning: Vault is still sealed after unseal attempt")
                        else:
                            print("Warning: Not enough unseal keys found in .env file")
                    else:
                        print("Warning: No .env file found with unseal keys")
                
                return [], ""

            # Give vault a moment to settle after starting
            time.sleep(5)
            
            # Initialize vault
            init_response = requests.put(
                "http://127.0.0.1:8200/v1/sys/init",
                json={"secret_shares": 5, "secret_threshold": 3}
            ).json()

            # Unseal vault with first 3 keys
            print("Unsealing vault...")
            for key in init_response["keys"][:3]:
                unseal_response = requests.put(
                    "http://127.0.0.1:8200/v1/sys/unseal",
                    json={"key": key}
                ).json()
                print(f"Unseal progress: {unseal_response.get('progress', 0)}/3")
            
            # Verify unseal was successful
            time.sleep(2)
            seal_status = requests.get("http://127.0.0.1:8200/v1/sys/seal-status").json()
            if not seal_status.get("sealed", True):
                print("Vault unsealed successfully")
            else:
                raise Exception("Vault is still sealed after unseal attempt")

            return init_response["keys"], init_response["root_token"]

        except Exception as e:
            raise Exception(f"Failed to initialize Vault: {str(e)}")

    def save_credentials(self, keys: List[str], token: str) -> None:
        """Save unseal keys and token to .env file."""
        # Skip if vault was already initialized
        if not keys and not token:
            print("Skipping credential save - vault already initialized")
            return
            
        # Create parent directory if it doesn't exist
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        
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
        self.env_file.chmod(0o600)  # Secure the file

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
