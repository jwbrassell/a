#!/usr/bin/env python3
"""
Script to reinitialize Vault policies without restarting the server
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.utils.vault_defaults import initialize_vault_policies
from vault_utility import VaultUtility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reinitialize_policies():
    """Reinitialize Vault policies."""
    try:
        # Initialize VaultUtility
        vault_util = VaultUtility()
        
        # Initialize policies
        if initialize_vault_policies():
            logger.info("Successfully reinitialized Vault policies")
            return True
        else:
            logger.error("Failed to reinitialize Vault policies")
            return False
            
    except Exception as e:
        logger.error(f"Error reinitializing policies: {e}")
        return False

if __name__ == "__main__":
    reinitialize_policies()
