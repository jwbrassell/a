#!/usr/bin/env python3
"""Initialize default permissions in the database."""

from app import create_app, db
from app.models.permission import Permission
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_permissions(app=None):
    """Initialize default permissions."""
    if app is None:
        app = create_app()
    
    with app.app_context():
        logger.info("Starting permission initialization...")
        
        try:
            Permission.initialize_default_permissions()
            logger.info("Default permissions initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during permission initialization: {e}")
            raise

def main():
    """Main entry point when run directly."""
    app = create_app()
    init_permissions(app)

if __name__ == '__main__':
    main()
