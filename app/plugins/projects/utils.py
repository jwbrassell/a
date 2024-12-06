"""Utility functions for the projects plugin."""

from app.extensions import db
from .models import ProjectStatus, ProjectPriority

def init_project_settings():
    """Initialize project statuses and priorities if they don't exist."""
    # Default statuses
    default_statuses = [
        ('New', 'primary'),
        ('In Progress', 'info'),
        ('On Hold', 'warning'),
        ('Completed', 'success'),
        ('Cancelled', 'danger'),
        ('Archived', 'secondary')
    ]
    
    # Default priorities
    default_priorities = [
        ('Low', 'success'),
        ('Medium', 'warning'),
        ('High', 'danger')
    ]
    
    # Create statuses
    for name, color in default_statuses:
        if not ProjectStatus.query.filter_by(name=name).first():
            status = ProjectStatus(name=name, color=color)
            db.session.add(status)
    
    # Create priorities
    for name, color in default_priorities:
        if not ProjectPriority.query.filter_by(name=name).first():
            priority = ProjectPriority(name=name, color=color)
            db.session.add(priority)
    
    db.session.commit()
