from functools import wraps
from flask import request
from flask_login import current_user
from app import db
from app.models import UserActivity
from app.logging_utils import log_error

def track_activity(f):
    """
    Decorator to track user activity for a route.
    Automatically logs the route access and user information.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Record the activity before executing the route
            activity = UserActivity(
                user_id=current_user.id if current_user.is_authenticated else None,
                username=current_user.username if current_user.is_authenticated else None,
                activity=f"Accessed {request.endpoint}"
            )
            db.session.add(activity)
            db.session.commit()
            
            # Execute the route
            return f(*args, **kwargs)
            
        except Exception as e:
            log_error(f"Error tracking activity: {str(e)}")
            db.session.rollback()
            # Continue with the route execution even if tracking fails
            return f(*args, **kwargs)
            
    return decorated_function
