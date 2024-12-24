#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

class AppSetup:
    def __init__(self, token: Optional[str] = None):
        self.env_file = Path(".env")
        self.vault_env = Path("setup/.env.vault")
        self.token = token
        self.vault_addr = "http://127.0.0.1:8200"

    def load_vault_env(self) -> None:
        """Load Vault environment if no token provided."""
        if not self.token and self.vault_env.exists():
            load_dotenv(self.vault_env)
            self.token = os.getenv("VAULT_TOKEN")
        
        if not self.token:
            raise Exception("No Vault token provided and couldn't load from .env.vault")

    def verify_vault_connection(self) -> None:
        """Verify Vault is accessible and token is valid."""
        try:
            # Check Vault health
            health_response = requests.get(f"{self.vault_addr}/v1/sys/health")
            if health_response.status_code not in (200, 429):  # 429 means unsealed but in standby
                raise Exception("Vault is not healthy")
            
            # Verify token
            headers = {"X-Vault-Token": self.token}
            auth_response = requests.get(f"{self.vault_addr}/v1/auth/token/lookup-self", headers=headers)
            if auth_response.status_code != 200:
                raise Exception("Invalid Vault token")

        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Vault. Is it running?")
        except Exception as e:
            raise Exception(f"Failed to verify Vault connection: {str(e)}")

    def setup_vault_policies(self) -> None:
        """Set up necessary Vault policies for the application."""
        try:
            headers = {"X-Vault-Token": self.token}
            
            # Create a policy for the application
            app_policy = {
                "policy": """
                # Allow reading secrets from specific paths
                path "secret/data/app/*" {
                    capabilities = ["read", "list"]
                }
                
                # Allow the app to renew its token
                path "auth/token/renew-self" {
                    capabilities = ["update"]
                }
                """
            }
            
            response = requests.put(
                f"{self.vault_addr}/v1/sys/policies/acl/app-policy",
                headers=headers,
                json=app_policy
            )
            
            if response.status_code != 204:
                raise Exception("Failed to create Vault policy")

        except Exception as e:
            raise Exception(f"Failed to setup Vault policies: {str(e)}")

    def create_app_token(self) -> str:
        """Create a token for the application with appropriate policies."""
        try:
            headers = {"X-Vault-Token": self.token}
            
            token_request = {
                "policies": ["app-policy"],
                "renewable": True,
                "ttl": "768h",  # 32 days
                "display_name": "flask-app"
            }
            
            response = requests.post(
                f"{self.vault_addr}/v1/auth/token/create",
                headers=headers,
                json=token_request
            ).json()
            
            return response["auth"]["client_token"]

        except Exception as e:
            raise Exception(f"Failed to create app token: {str(e)}")

    def update_env_file(self, app_token: str) -> None:
        """Update or create .env file with Vault configuration."""
        env_content = f"""
VAULT_ADDR={self.vault_addr}
VAULT_TOKEN={app_token}
FLASK_APP=app.py
FLASK_ENV=production
        """.strip()
        
        # Preserve existing env vars if file exists
        if self.env_file.exists():
            current_env = self.env_file.read_text()
            # Remove any existing VAULT_ variables
            current_env = "\n".join(
                line for line in current_env.splitlines()
                if not line.startswith("VAULT_")
            )
            env_content = f"{current_env}\n{env_content}"
        
        self.env_file.write_text(env_content)
        self.env_file.chmod(0o600)

    def setup(self) -> None:
        """Run the complete setup process."""
        print("Starting Flask app setup with Vault integration...")
        
        print("Loading Vault environment...")
        self.load_vault_env()
        
        print("Verifying Vault connection...")
        self.verify_vault_connection()
        
        print("Setting up Vault policies...")
        self.setup_vault_policies()
        
        print("Creating application token...")
        app_token = self.create_app_token()
        
        print("Updating environment file...")
        self.update_env_file(app_token)
        
        print(f"""
Flask app setup complete!
- Vault policies configured
- Application token created
- Environment file updated at {self.env_file}
        """.strip())

def main():
    parser = argparse.ArgumentParser(description="Setup Flask application with Vault integration")
    parser.add_argument("--token", help="Vault root token (optional if .env.vault exists)")
    
    args = parser.parse_args()
    
    try:
        setup = AppSetup(token=args.token)
        setup.setup()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
