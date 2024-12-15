"""Vault utilities for the reports plugin."""

from vault_utility import VaultUtility
from flask import current_app
import json

class ReportsVaultManager:
    """Manages vault operations for the reports plugin."""
    
    def __init__(self):
        self.vault = VaultUtility()
        
    def store_database_credentials(self, db_id, credentials):
        """Store database credentials in vault.
        
        Args:
            db_id: Database connection ID
            credentials: Dict containing credentials (username, password)
        """
        try:
            # Store credentials in vault
            self.vault.plugin_credentials.store_plugin_credentials(
                f'reports_db_{db_id}',
                credentials
            )
        except Exception as e:
            current_app.logger.error(f"Error storing credentials in vault: {str(e)}")
            raise
            
    def get_database_credentials(self, db_id):
        """Retrieve database credentials from vault.
        
        Args:
            db_id: Database connection ID
            
        Returns:
            Dict containing credentials (username, password)
        """
        try:
            credentials = self.vault.plugin_credentials.get_plugin_credentials(
                f'reports_db_{db_id}'
            )
            if not credentials:
                raise ValueError(f"No credentials found for database {db_id}")
            return credentials
        except Exception as e:
            current_app.logger.error(f"Error retrieving credentials from vault: {str(e)}")
            raise
            
    def update_database_credentials(self, db_id, credentials):
        """Update database credentials in vault.
        
        Args:
            db_id: Database connection ID
            credentials: Dict containing new credentials (username, password)
        """
        try:
            self.vault.plugin_credentials.rotate_plugin_credentials(
                f'reports_db_{db_id}',
                credentials
            )
        except Exception as e:
            current_app.logger.error(f"Error updating credentials in vault: {str(e)}")
            raise
            
    def delete_database_credentials(self, db_id):
        """Delete database credentials from vault.
        
        Args:
            db_id: Database connection ID
        """
        try:
            # Note: This assumes vault utility has a delete method
            # If not available, implement appropriate cleanup
            self.vault.plugin_credentials.delete_plugin_credentials(
                f'reports_db_{db_id}'
            )
        except Exception as e:
            current_app.logger.error(f"Error deleting credentials from vault: {str(e)}")
            raise

# Create singleton instance
vault_manager = ReportsVaultManager()
