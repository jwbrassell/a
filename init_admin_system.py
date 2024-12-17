#!/usr/bin/env python3
"""Initialize the admin system database and default configurations."""

from app import create_app, db
from app.models.metrics import init_metrics_models
from app.utils.role_templates import initialize_default_roles
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables."""
    try:
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def init_admin_system():
    """Initialize the complete admin system."""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting admin system initialization...")
        
        # Initialize database
        if not init_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize metrics models
        try:
            logger.info("Initializing metrics models...")
            init_metrics_models()
            logger.info("Metrics models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing metrics models: {e}")
            return False
        
        # Initialize default roles
        try:
            logger.info("Initializing default roles...")
            initialize_default_roles()
            logger.info("Default roles initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing default roles: {e}")
            return False
        
        logger.info("Admin system initialization completed successfully")
        return True

if __name__ == '__main__':
    success = init_admin_system()
    if not success:
        logger.error("Admin system initialization failed")
        exit(1)
