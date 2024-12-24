
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
                    # We'll handle this in create_config by setting disable_mlock=true
                
                # Ensure vault binary is accessible
                os.environ["PATH"] = f"{self.vault_dir}:{os.environ['PATH']}"
            
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
        # Check if we need to disable mlock (if setcap failed on Linux)
        disable_mlock = True  # Always true for our localhost setup
        
        config = f"""
storage "file" {{
    path = "{self.vault_data}"
}}

listener "tcp" {{
    address = "127.0.0.1:8200"
    tls_disable = 1
}}

api_addr = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"
disable_mlock = {str(disable_mlock).lower()}
ui = false
        """
        self.vault_config.write_text(config.strip())
        self.vault_config.chmod(0o600)  # Secure the config file

    def start_vault(self) -> None:
        """Start Vault server."""
        try:
            # Ensure the binary is in PATH
            if self.is_linux:
                os.environ["PATH"] = f"{self.vault_dir}:{os.environ['PATH']}"
            
            # Set environment variable
            os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
            
            # Start vault server with log file
            log_file = Path("vault.log")
            with open(log_file, "w") as log:
                if self.is_linux:
                    # On Linux, use start-stop-daemon to properly daemonize the process
                    cmd = [
                        "start-stop-daemon",
                        "--start",
                        "--background",
                        "--make-pidfile",
                        "--pidfile", str(self.pid_file),
                        "--exec", str(self.vault_bin),
                        "--",
                        "server",
                        "-config", str(self.vault_config)
                    ]
                    subprocess.run(cmd, check=True, stdout=log, stderr=log)
                else:
                    # On macOS, use the original method
                    process = subprocess.Popen(
                        [str(self.vault_bin), "server", "-config", str(self.vault_config)],
                        stdout=log,
                        stderr=log,
                        start_new_session=True
                    )
                    # Save PID
                    self.pid_file.write_text(str(process.pid))
            
            # Secure the PID file
            self.pid_file.chmod(0o600)
            
            # Wait for Vault to start and verify it's running
            max_attempts = 15  # Increased attempts
            for attempt in range(max_attempts):
                try:
                    time.sleep(2)  # Give Vault time to start
                    
                    # Try to check Vault status
                    response = requests.get("http://127.0.0.1:8200/v1/sys/health")
                    if response.status_code in (200, 429, 472, 473):  # Various Vault status codes
                        print(f"Vault is starting (attempt {attempt + 1}/{max_attempts})")
                        if response.status_code == 200:
                            print("Vault is now running!")
                            break
                except requests.exceptions.ConnectionError:
                    print(f"Waiting for Vault to start (attempt {attempt + 1}/{max_attempts})")
                
                # On the last attempt, check logs and raise error
                if attempt == max_attempts - 1:
                    if log_file.exists():
                        log_content = log_file.read_text()
                        print(f"Vault log contents:\n{log_content}")
                    
                    # Check if process is actually running
                    if self.is_linux:
                        try:
                            with open(self.pid_file) as f:
                                pid = int(f.read().strip())
                            os.kill(pid, 0)  # Check if process exists
                            print(f"Process {pid} exists but Vault is not responding")
                        except (ProcessLookupError, ValueError, FileNotFoundError):
                            print("Vault process is not running")
                    
                    raise Exception("Vault failed to start. Check vault.log for details.")

        except Exception as e:
            # Clean up PID file if startup failed
            if self.pid_file.exists():
                self.pid_file.unlink()
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
