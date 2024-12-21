"""Script to update admin permissions for existing installations."""

from flask import Flask
from app import create_app
from app.utils.init_db import init_admin_permissions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_permissions():
    """Update admin permissions."""
    app = create_app()
    with app.app_context():
        logger.info("Updating admin permissions...")
        if init_admin_permissions():
            logger.info("Successfully updated admin permissions")
        else:
            logger.error("Failed to update admin permissions")

if __name__ == '__main__':
    update_permissions()
