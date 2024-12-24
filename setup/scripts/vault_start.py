#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from typing import List
from dotenv import load_dotenv

class VaultStarter:
    def __init__(self):
        self.vault_dir = Path.home() / ".vault"
        self.vault_bin = self.vault_dir / "vault"
        self.vault_config = self.vault_dir / "config.hcl"
        self.env_file = Path("setup/.env.vault")
        self.pid_file = Path("vault.pid")

    def load_environment(self) -> None:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            raise Exception(f"Environment file not found: {self.env_file}")
        
        load_dotenv(self.env_file)
        
        # Verify required variables
        required_vars = [
            "VAULT_ADDR",
            "VAULT_UNSEAL_KEY_1",
            "VAULT_UNSEAL_KEY_2",
            "VAULT_UNSEAL_KEY_3"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise Exception(f"Missing required environment variables: {', '.join(missing)}")

    def start_vault(self) -> None:
        """Start the Vault server."""
        try:
            # Check if Vault is already running
            if self.pid_file.exists():
                print("Vault appears to be already running.")
                return
            
            # Start vault server
            process = subprocess.Popen(
                [str(self.vault_bin), "server", "-config", str(self.vault_config)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            
            # Wait for Vault to start
            time.sleep(2)
            
            # Check if Vault is running
            for _ in range(5):  # Try 5 times
                try:
                    requests.get(os.getenv("VAULT_ADDR") + "/v1/sys/health")
                    break
                except requests.exceptions.ConnectionError:
                    time.sleep(2)
            else:
                raise Exception("Vault failed to start")

        except Exception as e:
            raise Exception(f"Failed to start Vault: {str(e)}")

    def unseal_vault(self) -> None:
        """Unseal the Vault using the first three unseal keys."""
        try:
            # Get unseal keys from environment
            unseal_keys = [
                os.getenv(f"VAULT_UNSEAL_KEY_{i}")
                for i in range(1, 4)  # We only need 3 keys
            ]
            
            # Unseal with each key
            for key in unseal_keys:
                response = requests.put(
                    os.getenv("VAULT_ADDR") + "/v1/sys/unseal",
                    json={"key": key}
                ).json()
                
                if response.get("sealed") is False:
                    break  # Vault is unsealed
            
            if response.get("sealed", True):
                raise Exception("Failed to unseal Vault")

        except Exception as e:
            raise Exception(f"Failed to unseal Vault: {str(e)}")

    def verify_vault_status(self) -> None:
        """Verify that Vault is unsealed and ready."""
        try:
            response = requests.get(os.getenv("VAULT_ADDR") + "/v1/sys/health").json()
            
            if response.get("sealed", True):
                raise Exception("Vault is still sealed")
            
            if not response.get("initialized", False):
                raise Exception("Vault is not initialized")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to verify Vault status: {str(e)}")

    def start(self) -> None:
        """Run the complete start and unseal process."""
        print("Starting Vault...")
        
        print("Loading environment...")
        self.load_environment()
        
        print("Starting Vault server...")
        self.start_vault()
        
        print("Unsealing Vault...")
        self.unseal_vault()
        
        print("Verifying Vault status...")
        self.verify_vault_status()
        
        print("""
Vault is now:
- Running
- Unsealed
- Ready for connections
        """.strip())

if __name__ == "__main__":
    try:
        starter = VaultStarter()
        starter.start()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
