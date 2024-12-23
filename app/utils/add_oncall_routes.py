"""Utility function to add on-call rotation management routes."""

from flask import current_app
from app.blueprints.oncall import init_app as init_oncall

def add_oncall_routes():
    """Initialize on-call rotation management routes."""
    try:
        init_oncall(current_app)
        return True
    except Exception as e:
        current_app.logger.error(f"Error initializing on-call routes: {e}")
        return False
