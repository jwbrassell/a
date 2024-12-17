#!/usr/bin/env python3
"""Initialize role templates in the database."""

from app import create_app, db
from app.utils.role_templates import initialize_default_roles
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize role templates."""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting role template initialization...")
        
        try:
            success = initialize_default_roles()
            if success:
                logger.info("Role templates initialized successfully")
            else:
                logger.error("Failed to initialize role templates")
                
        except Exception as e:
            logger.error(f"Error during role template initialization: {e}")
            raise

if __name__ == '__main__':
    main()
