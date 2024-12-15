#!/usr/bin/env python3
"""
Script to migrate existing database credentials from the database to vault.
This is a one-time migration script that should be run after the database
migration that removes the password field.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import text

# Add application root to Python path
app_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_root))

from app import create_app, db
from app.plugins.reports.models import DatabaseConnection
from app.plugins.reports.vault_utils import vault_manager

def migrate_credentials():
    """Migrate database credentials to vault."""
    app = create_app()
    
    with app.app_context():
        # Get all active database connections
        connections = DatabaseConnection.query.filter_by(is_active=True).all()
        
        print(f"Found {len(connections)} active database connections")
        
        for conn in connections:
            try:
                # Get password from database before it's removed
                password = db.session.execute(
                    text('SELECT password FROM database_connection WHERE id = :id'),
                    {'id': conn.id}
                ).scalar()
                
                if password:
                    print(f"Migrating credentials for database: {conn.name}")
                    
                    # Store both username and password in vault
                    vault_manager.store_database_credentials(
                        conn.id,
                        {
                            'username': conn.username,
                            'password': password
                        }
                    )
                    
                    print(f"Successfully migrated credentials for: {conn.name}")
                else:
                    print(f"No password found for database: {conn.name}")
                    
            except Exception as e:
                print(f"Error migrating credentials for {conn.name}: {str(e)}")
                
        print("\nMigration complete!")

if __name__ == '__main__':
    migrate_credentials()
