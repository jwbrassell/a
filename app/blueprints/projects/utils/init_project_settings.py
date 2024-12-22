"""Initialize project settings."""

from app.extensions import db
from app.models import Role, User
from ..models import ProjectStatus, ProjectPriority
import logging

logger = logging.getLogger(__name__)

def init_project_settings():
    """Initialize project settings."""
    try:
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            logger.warning("Admin user not found, skipping project settings initialization")
            return False
        
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
                logger.debug(f"Created project status: {name}")
        
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
                logger.debug(f"Created project priority: {name}")
        
        db.session.commit()
        logger.info("Project settings initialized successfully")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project settings: {str(e)}")
        return False
