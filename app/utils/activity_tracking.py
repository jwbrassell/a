from functools import wraps
from datetime import datetime
from flask import request, current_app
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
        # Import models here to avoid circular imports
        from app.plugins.admin.models import FeatureUsage, ResourceMetric
        
        start_time = datetime.utcnow()
        feature_usage = None
        
        try:
            # Only track activity for authenticated users
            if current_user.is_authenticated:
                # Track basic activity
                activity = UserActivity(
                    user_id=current_user.id,
                    username=current_user.username,
                    activity=f"Accessed {request.endpoint}"
                )
                db.session.add(activity)
                
                # Track feature usage
                if '.' in request.endpoint:
                    plugin, feature = request.endpoint.split('.', 1)
                    feature_usage = FeatureUsage(
                        timestamp=start_time,
                        feature=feature,
                        plugin=plugin,
                        user_id=current_user.id,
                        success=True
                    )
                    db.session.add(feature_usage)
                
                db.session.commit()
            
            # Execute the route
            result = f(*args, **kwargs)
            
            # Update feature usage with duration if it exists
            if current_user.is_authenticated and feature_usage is not None:
                try:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    feature_usage.duration = int(duration)
                    
                    # Track resource metrics
                    resource_metric = ResourceMetric(
                        timestamp=datetime.utcnow(),
                        resource_type='time',
                        category=request.endpoint,
                        value=duration,
                        unit='seconds'
                    )
                    db.session.add(resource_metric)
                    
                    # Track memory usage if available
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
                        memory_metric = ResourceMetric(
                            timestamp=datetime.utcnow(),
                            resource_type='memory',
                            category=request.endpoint,
                            value=memory_usage,
                            unit='MB'
                        )
                        db.session.add(memory_metric)
                    except:
                        pass  # Skip memory tracking if psutil is not available
                    
                    db.session.commit()
                except Exception as e:
                    log_error(f"Error updating metrics: {str(e)}")
                    db.session.rollback()
            
            return result
            
        except Exception as e:
            log_error(f"Error tracking activity: {str(e)}")
            db.session.rollback()
            
            # Track error in feature usage
            if current_user.is_authenticated and '.' in request.endpoint:
                try:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    error_feature = FeatureUsage(
                        timestamp=datetime.utcnow(),
                        feature=request.endpoint.split('.', 1)[1],
                        plugin=request.endpoint.split('.', 1)[0],
                        user_id=current_user.id,
                        success=False,
                        duration=int(duration)
                    )
                    db.session.add(error_feature)
                    db.session.commit()
                except:
                    pass  # Skip error tracking if it fails
            
            # Continue with the route execution even if tracking fails
            return f(*args, **kwargs)
            
    return decorated_function

def track_resource_usage(resource_type, category, value, unit):
    """
    Utility function to track arbitrary resource usage
    
    Args:
        resource_type (str): Type of resource (time, memory, storage, etc.)
        category (str): Category or context of the resource usage
        value (float): Value of the resource usage
        unit (str): Unit of measurement
    """
    try:
        if current_user.is_authenticated:
            from app.plugins.admin.models import ResourceMetric
            metric = ResourceMetric(
                timestamp=datetime.utcnow(),
                resource_type=resource_type,
                category=category,
                value=value,
                unit=unit
            )
            db.session.add(metric)
            db.session.commit()
    except Exception as e:
        log_error(f"Error tracking resource usage: {str(e)}")
        db.session.rollback()

def track_feature_usage(feature, plugin, duration=None, success=True):
    """
    Utility function to track feature usage manually
    
    Args:
        feature (str): Name of the feature
        plugin (str): Name of the plugin
        duration (int, optional): Duration in seconds
        success (bool): Whether the feature usage was successful
    """
    try:
        if current_user.is_authenticated:
            from app.plugins.admin.models import FeatureUsage
            usage = FeatureUsage(
                timestamp=datetime.utcnow(),
                feature=feature,
                plugin=plugin,
                user_id=current_user.id,
                duration=duration,
                success=success
            )
            db.session.add(usage)
            db.session.commit()
    except Exception as e:
        log_error(f"Error tracking feature usage: {str(e)}")
        db.session.rollback()
