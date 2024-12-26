#!/usr/bin/env python3
"""WSGI entry point for the Flask application."""
import os
import logging
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the Flask application
env = os.getenv('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == '__main__':
    app.run()
