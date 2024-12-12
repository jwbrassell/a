from functools import wraps
from flask import request
from flask_login import current_user
from app import db
from app.models import UserActivity
from app.logging_utils import log_error

def track_activity(f):
    """
    Decorator to track user activity for a route.
    Only tracks activity for authenticated users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Only track activity for authenticated users
            if current_user.is_authenticated:
                activity = UserActivity(
                    user_id=current_user.id,
                    username=current_user.username,
                    activity=f"Accessed {request.endpoint}"
                )
                db.session.add(activity)
                db.session.commit()  # Commit the activity immediately
            
            # Execute the route
            return f(*args, **kwargs)
            
        except Exception as e:
            log_error(f"Error tracking activity: {str(e)}")
            db.session.rollback()
            # Continue with the route execution even if tracking fails
            return f(*args, **kwargs)
            
    return decorated_function
