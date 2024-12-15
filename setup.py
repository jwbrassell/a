#!/usr/bin/env python3
"""
Setup script for initializing the application.

This script provides a modular setup process with options to:
1. Choose database type (SQLite/MariaDB)
2. Initialize core data and navigation
3. Initialize plugin data
4. Set up Vault integration
5. Configure environment settings

Usage:
    python setup.py                  # Full setup with SQLite in dev mode
    python setup.py --mariadb       # Use MariaDB instead of SQLite
    python setup.py --env prod      # Production environment setup
    python setup.py --skip-vault    # Skip Vault setup
    python setup.py --skip-plugins  # Skip plugin initialization
"""

from utils.setup.main import setup

if __name__ == "__main__":
    setup()
