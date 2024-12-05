from flask import request, current_app
from flask_login import current_user
from app import db
from app.models import PageVisit

def log_page_visit(response=None):
    """
    Log a page visit to the database.
    Can be used both before and after request to capture both attempts and results.
    """
    try:
        # Skip logging for static files
        if request.path.startswith('/static/'):
            return response

        # Get user info if authenticated
        user_id = current_user.id if current_user.is_authenticated else None
        username = current_user.username if current_user.is_authenticated else None

        # Create page visit record
        visit = PageVisit(
            route=request.path,
            method=request.method,
            status_code=response.status_code if response else 0,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )

        db.session.add(visit)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(f"Error logging page visit: {str(e)}")
        db.session.rollback()

    return response if response else None

def log_info(message):
    """
    Log an info message with user context.
    
    Args:
        message: The message to log
    """
    try:
        user_context = f"[User: {current_user.username}]" if current_user.is_authenticated else "[Anonymous]"
        current_app.logger.info(f"{user_context} {message}")
    except Exception as e:
        current_app.logger.error(f"Error in log_info: {str(e)}")

def log_error(message, exc_info=False):
    """
    Log an error message with user context and optional exception info.
    
    Args:
        message: The error message to log
        exc_info: Whether to include exception traceback (default: False)
    """
    try:
        user_context = f"[User: {current_user.username}]" if current_user.is_authenticated else "[Anonymous]"
        current_app.logger.error(f"{user_context} {message}", exc_info=exc_info)
    except Exception as e:
        current_app.logger.error(f"Error in log_error: {str(e)}")

def log_warning(message):
    """
    Log a warning message with user context.
    
    Args:
        message: The warning message to log
    """
    try:
        user_context = f"[User: {current_user.username}]" if current_user.is_authenticated else "[Anonymous]"
        current_app.logger.warning(f"{user_context} {message}")
    except Exception as e:
        current_app.logger.error(f"Error in log_warning: {str(e)}")
