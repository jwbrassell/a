"""Initialize project settings."""

from app import db
from app.models import Role, User
from ..models import ProjectStatus, ProjectPriority

def init_project_settings():
    """Initialize project settings."""
    # Get admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        return
    
    # Initialize default project statuses if they don't exist
    default_statuses = [
        ('active', 'success'),
        ('on_hold', 'warning'),
        ('completed', 'info'),
        ('cancelled', 'danger')
    ]
    
    for name, color in default_statuses:
        if not ProjectStatus.query.filter_by(name=name).first():
            status = ProjectStatus(
                name=name,
                color=color,
                created_by=admin_user.username
            )
            db.session.add(status)
    
    # Initialize default project priorities if they don't exist
    default_priorities = [
        ('low', 'info'),
        ('medium', 'warning'),
        ('high', 'danger')
    ]
    
    for name, color in default_priorities:
        if not ProjectPriority.query.filter_by(name=name).first():
            priority = ProjectPriority(
                name=name,
                color=color,
                created_by=admin_user.username
            )
            db.session.add(priority)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing project settings: {str(e)}")
