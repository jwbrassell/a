"""Activity tracking plugin for Flask application."""
from flask import Blueprint, request, current_app
from flask_login import current_user
from app import db
from app.models import UserActivity, PageVisit
from app.logging_utils import log_error
from app.utils.plugin_manager import PluginMetadata

# Define plugin metadata
plugin_metadata = PluginMetadata(
    name="Activity Tracking",
    version="1.0.0",
    description="User activity and page visit tracking",
    author="System",
    required_roles=["admin"],
    icon="fa-chart-line",
    category="admin",
    weight=90
)

# Create blueprint
bp = Blueprint('tracking', __name__)

@bp.before_app_request
def track_request_start():
    """Track the start of each request."""
    try:
        # Skip tracking for static files and specific paths
        if request.path.startswith('/static/'):
            return None
            
        # Track authenticated user activity
        if current_user.is_authenticated:
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Accessed {request.endpoint or request.path} [{request.method}]"
            )
            db.session.add(activity)
            db.session.commit()
            
    except Exception as e:
        log_error(f"Error in track_request_start: {str(e)}")
        db.session.rollback()

@bp.after_app_request
def track_request_end(response):
    """Track the completion of each request."""
    try:
        # Skip tracking for static files with 304 status
        if request.path.startswith('/static/') and response.status_code == 304:
            return response
            
        # Skip tracking for all static files
        if request.path.startswith('/static/'):
            return response
            
        # Get user info if authenticated
        user_id = current_user.id if current_user.is_authenticated else None
        username = current_user.username if current_user.is_authenticated else None
        
        # Create page visit record
        visit = PageVisit(
            route=request.path,
            method=request.method,
            status_code=response.status_code,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        
        db.session.add(visit)
        db.session.commit()
        
    except Exception as e:
        log_error(f"Error in track_request_end: {str(e)}")
        db.session.rollback()
        
    return response
