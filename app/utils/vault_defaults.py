"""Default Vault KV structure initialization"""
from flask import current_app
import logging

logger = logging.getLogger(__name__)

DEFAULT_KV_STRUCTURE = {
    "app": {
        "settings": {
            "environment": "development",
            "maintenance_mode": False,
            "debug_mode": False
        },
        "monitoring": {
            "last_health_check": "",
            "status": "unknown",
            "sealed": True
        }
    },
    "plugins": {
        # Plugin-specific credentials will be stored here
        # Format: plugin_name: { credentials: {}, settings: {} }
    }
}

def initialize_vault_structure():
    """Initialize the default KV structure in Vault"""
    try:
        vault = current_app.vault

        # Initialize app settings
        if not vault.get_secret("app/settings"):
            vault.store_secret("app/settings", DEFAULT_KV_STRUCTURE["app"]["settings"])
            logger.info("Initialized app settings in Vault")

        # Initialize monitoring data
        if not vault.get_secret("app/monitoring"):
            vault.store_secret("app/monitoring", DEFAULT_KV_STRUCTURE["app"]["monitoring"])
            logger.info("Initialized monitoring data in Vault")

        # Initialize plugins structure
        if not vault.get_secret("plugins"):
            vault.store_secret("plugins", {})
            logger.info("Initialized plugins structure in Vault")

        logger.info("Vault KV structure initialization complete")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Vault KV structure: {e}")
        return False
