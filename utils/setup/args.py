"""
Command line argument parsing for application setup
"""
import argparse

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Setup the application with various configuration options.'
    )
    parser.add_argument(
        '--mariadb',
        action='store_true',
        help='Use MariaDB instead of SQLite'
    )
    parser.add_argument(
        '--env',
        choices=['dev', 'prod'],
        default='dev',
        help='Environment to configure (dev or prod)'
    )
    parser.add_argument(
        '--skip-vault',
        action='store_true',
        help='Skip Vault setup'
    )
    parser.add_argument(
        '--skip-plugins',
        action='store_true',
        help='Skip plugin initialization'
    )
    return parser.parse_args()
