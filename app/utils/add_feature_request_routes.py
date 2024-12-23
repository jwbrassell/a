from flask import current_app
from app.blueprints.feature_requests.plugin import init_app as init_feature_requests

def add_feature_request_routes():
    """Initialize feature requests blueprint."""
    try:
        init_feature_requests(current_app)
        return True
    except Exception as e:
        current_app.logger.error(f"Error initializing feature requests blueprint: {e}")
        return False
