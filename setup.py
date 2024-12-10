#!/usr/bin/env python3
"""
Setup script for initializing the application.
This script:
1. Creates a new database if it doesn't exist
2. Runs all migrations
3. Initializes default data
"""

import os
import subprocess
from app import create_app
from flask_migrate import upgrade
from init_database_values import main as init_db

def setup():
    """Run the complete setup process"""
    print("Starting application setup...")
    
    # Create instance directory if it doesn't exist
    instance_path = "instance"
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print("Created instance directory")
    
    # Remove existing database if it exists
    db_path = os.path.join(instance_path, "app.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Run all migrations
        print("\nApplying database migrations...")
        upgrade()
        
        # Initialize database with default values
        print("\nInitializing database values...")
        init_db()
    
    print("\nSetup complete!")
    print("\nYou can now start the application with:")
    print("flask run")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: test123")

if __name__ == "__main__":
    setup()
