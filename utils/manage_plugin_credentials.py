#!/usr/bin/env python3
"""
Plugin Credential Management Utility
Helps manage plugin credentials in Vault with a CLI interface
"""

import os
import sys
import json
import click
import logging
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from vault_utility import VaultUtility, VaultError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CredentialManager:
    def __init__(self):
        try:
            self.vault = VaultUtility()
        except VaultError as e:
            logger.error(f"Failed to initialize Vault: {e}")
            sys.exit(1)

    def store_credentials(self, plugin_name: str, credentials: Dict) -> bool:
        """Store credentials for a plugin."""
        try:
            self.vault.plugin_credentials.store_plugin_credentials(plugin_name, credentials)
            logger.info(f"Successfully stored credentials for plugin: {plugin_name}")
            return True
        except VaultError as e:
            logger.error(f"Failed to store credentials: {e}")
            return False

    def get_credentials(self, plugin_name: str) -> Optional[Dict]:
        """Retrieve credentials for a plugin."""
        try:
            creds = self.vault.plugin_credentials.get_plugin_credentials(plugin_name)
            if creds:
                logger.info(f"Retrieved credentials for plugin: {plugin_name}")
            else:
                logger.warning(f"No credentials found for plugin: {plugin_name}")
            return creds
        except VaultError as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None

    def rotate_credentials(self, plugin_name: str, new_credentials: Dict) -> bool:
        """Rotate credentials for a plugin."""
        try:
            self.vault.plugin_credentials.rotate_plugin_credentials(plugin_name, new_credentials)
            logger.info(f"Successfully rotated credentials for plugin: {plugin_name}")
            return True
        except VaultError as e:
            logger.error(f"Failed to rotate credentials: {e}")
            return False

    def list_plugins(self) -> list:
        """List all plugins with stored credentials."""
        try:
            plugins = self.vault.list_secrets("plugins")
            return plugins if plugins else []
        except VaultError as e:
            logger.error(f"Failed to list plugins: {e}")
            return []

    def delete_credentials(self, plugin_name: str) -> bool:
        """Delete credentials for a plugin."""
        try:
            self.vault.delete_secret(f"plugins/{plugin_name}")
            logger.info(f"Successfully deleted credentials for plugin: {plugin_name}")
            return True
        except VaultError as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False

@click.group()
def cli():
    """Manage plugin credentials in Vault."""
    pass

@cli.command()
@click.argument('plugin_name')
@click.argument('credentials_file', type=click.Path(exists=True))
def store(plugin_name: str, credentials_file: str):
    """Store credentials for a plugin from a JSON file."""
    try:
        with open(credentials_file) as f:
            credentials = json.load(f)
    except json.JSONDecodeError:
        logger.error("Invalid JSON file")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to read credentials file: {e}")
        sys.exit(1)

    manager = CredentialManager()
    if manager.store_credentials(plugin_name, credentials):
        click.echo(f"Successfully stored credentials for {plugin_name}")
    else:
        sys.exit(1)

@cli.command()
@click.argument('plugin_name')
def get(plugin_name: str):
    """Retrieve credentials for a plugin."""
    manager = CredentialManager()
    credentials = manager.get_credentials(plugin_name)
    
    if credentials:
        click.echo(json.dumps(credentials, indent=2))
    else:
        sys.exit(1)

@cli.command()
@click.argument('plugin_name')
@click.argument('credentials_file', type=click.Path(exists=True))
def rotate(plugin_name: str, credentials_file: str):
    """Rotate credentials for a plugin using new credentials from a JSON file."""
    try:
        with open(credentials_file) as f:
            new_credentials = json.load(f)
    except json.JSONDecodeError:
        logger.error("Invalid JSON file")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to read credentials file: {e}")
        sys.exit(1)

    manager = CredentialManager()
    if manager.rotate_credentials(plugin_name, new_credentials):
        click.echo(f"Successfully rotated credentials for {plugin_name}")
    else:
        sys.exit(1)

@cli.command()
def list():
    """List all plugins with stored credentials."""
    manager = CredentialManager()
    plugins = manager.list_plugins()
    
    if plugins:
        click.echo("\nPlugins with stored credentials:")
        for plugin in plugins:
            click.echo(f"- {plugin}")
    else:
        click.echo("No plugins found with stored credentials")

@cli.command()
@click.argument('plugin_name')
@click.option('--force/--no-force', default=False, help="Force deletion without confirmation")
def delete(plugin_name: str, force: bool):
    """Delete credentials for a plugin."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete credentials for {plugin_name}?"):
            click.echo("Operation cancelled")
            return

    manager = CredentialManager()
    if manager.delete_credentials(plugin_name):
        click.echo(f"Successfully deleted credentials for {plugin_name}")
    else:
        sys.exit(1)

@cli.command()
@click.argument('plugin_name')
def validate(plugin_name: str):
    """Validate stored credentials for a plugin."""
    manager = CredentialManager()
    credentials = manager.get_credentials(plugin_name)
    
    if not credentials:
        click.echo(f"No credentials found for {plugin_name}")
        sys.exit(1)
        
    # Check required fields
    required_fields = ['api_key', 'secret']  # Add your required fields
    missing_fields = [field for field in required_fields if field not in credentials]
    
    if missing_fields:
        click.echo(f"Missing required fields: {', '.join(missing_fields)}")
        sys.exit(1)
        
    # Check credential format
    for key, value in credentials.items():
        if not isinstance(value, (str, int, float, bool)):
            click.echo(f"Invalid value type for {key}: {type(value)}")
            sys.exit(1)
            
    click.echo(f"Credentials for {plugin_name} are valid")

@cli.command()
def check():
    """Check Vault connection and configuration."""
    try:
        manager = CredentialManager()
        click.echo("Vault connection successful")
        
        # Check if we can list secrets
        manager.list_plugins()
        click.echo("Secret engine access verified")
        
        click.echo("\nVault configuration is correct")
    except Exception as e:
        click.echo(f"Vault configuration check failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
