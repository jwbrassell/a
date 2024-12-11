#!/usr/bin/env python3
"""
Setup utilities for Black Friday Lunch application.
This module provides helper functions for common setup and maintenance tasks.
"""

import os
import sys
import subprocess
from typing import List, Dict, Optional

class SetupUtils:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.app_dir = os.path.join(self.root_dir, 'app')
        self.plugins_dir = os.path.join(self.app_dir, 'plugins')

    def check_environment(self) -> Dict[str, bool]:
        """
        Check if all required environment variables and dependencies are set up.
        
        Returns:
            Dict[str, bool]: Status of each environment check
        """
        checks = {
            'python_version': sys.version_info >= (3, 8),
            'env_file': os.path.exists(os.path.join(self.root_dir, '.env')),
            'requirements': os.path.exists(os.path.join(self.root_dir, 'requirements.txt')),
            'static_dirs': os.path.exists(os.path.join(self.app_dir, 'static'))
        }
        return checks

    def list_plugins(self) -> List[str]:
        """
        List all available plugins in the application.
        
        Returns:
            List[str]: Names of available plugins
        """
        if not os.path.exists(self.plugins_dir):
            return []
        
        return [d for d in os.listdir(self.plugins_dir) 
                if os.path.isdir(os.path.join(self.plugins_dir, d))
                and not d.startswith('__')]

    def verify_plugin_structure(self, plugin_name: str) -> Dict[str, bool]:
        """
        Verify that a plugin has all required files and directories.
        
        Args:
            plugin_name (str): Name of the plugin to verify
            
        Returns:
            Dict[str, bool]: Status of each structural check
        """
        plugin_dir = os.path.join(self.plugins_dir, plugin_name)
        if not os.path.exists(plugin_dir):
            return {}

        checks = {
            'init': os.path.exists(os.path.join(plugin_dir, '__init__.py')),
            'templates': os.path.exists(os.path.join(plugin_dir, 'templates')),
            'routes': any(f.endswith('routes.py') for f in os.listdir(plugin_dir))
        }
        return checks

    def check_database_setup(self) -> bool:
        """
        Check if the database is properly configured.
        
        Returns:
            bool: True if database setup appears valid
        """
        try:
            # Check for database initialization files
            required_files = [
                os.path.join(self.root_dir, 'init_db.py'),
                os.path.join(self.root_dir, 'config.py')
            ]
            return all(os.path.exists(f) for f in required_files)
        except Exception as e:
            print(f"Error checking database setup: {e}")
            return False

    def verify_static_files(self) -> Dict[str, bool]:
        """
        Verify that all required static files are present.
        
        Returns:
            Dict[str, bool]: Status of static file checks
        """
        static_dir = os.path.join(self.app_dir, 'static')
        checks = {
            'css': os.path.exists(os.path.join(static_dir, 'src', 'css')),
            'js': os.path.exists(os.path.join(static_dir, 'src', 'js')),
            'images': os.path.exists(os.path.join(static_dir, 'images')),
            'uploads': os.path.exists(os.path.join(static_dir, 'uploads'))
        }
        return checks

def main():
    """
    Main function to run setup utilities interactively.
    """
    utils = SetupUtils()
    
    print("Black Friday Lunch Setup Utilities")
    print("=================================")
    
    # Check environment
    env_checks = utils.check_environment()
    print("\nEnvironment Checks:")
    for check, status in env_checks.items():
        print(f"  {check}: {'✓' if status else '✗'}")
    
    # List plugins
    plugins = utils.list_plugins()
    print("\nInstalled Plugins:")
    for plugin in plugins:
        print(f"  - {plugin}")
        structure = utils.verify_plugin_structure(plugin)
        for check, status in structure.items():
            print(f"    {check}: {'✓' if status else '✗'}")
    
    # Check database
    db_status = utils.check_database_setup()
    print(f"\nDatabase Setup: {'✓' if db_status else '✗'}")
    
    # Check static files
    static_checks = utils.verify_static_files()
    print("\nStatic Files:")
    for check, status in static_checks.items():
        print(f"  {check}: {'✓' if status else '✗'}")

if __name__ == '__main__':
    main()
