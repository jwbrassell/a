#!/usr/bin/env python3
"""
Database Setup Script
This script sets up the database environment by:
1. Creating necessary directories
2. Setting proper permissions
3. Initializing the database
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database_environment():
    """Set up the database environment."""
    try:
        # Create instance directory if it doesn't exist
        instance_dir = Path('instance')
        instance_dir.mkdir(exist_ok=True)
        os.chmod(instance_dir, 0o777)  # Full permissions for development
        
        # Create cache directory
        cache_dir = instance_dir / 'cache'
        cache_dir.mkdir(exist_ok=True)
        os.chmod(cache_dir, 0o777)  # Full permissions for development
        
        # Create empty database file with proper permissions
        db_file = instance_dir / 'app.db'
        if not db_file.exists():
            db_file.touch()
        os.chmod(db_file, 0o666)  # Read/write for all users
        
        logger.info("Database environment setup complete")
        logger.info(f"Instance directory: {instance_dir.absolute()}")
        logger.info(f"Cache directory: {cache_dir.absolute()}")
        logger.info(f"Database file: {db_file.absolute()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up database environment: {e}")
        return False

def main():
    """Main entry point."""
    if setup_database_environment():
        logger.info("Database environment setup successful")
        sys.exit(0)
    else:
        logger.error("Database environment setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
