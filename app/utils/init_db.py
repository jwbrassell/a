"""Database initialization utilities."""

from flask import current_app
from app.extensions import db
import logging
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

def init_roles():
    """Initialize default roles if they don't exist."""
    try:
        from app.models.role import Role

        # Check if Admin role exists
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            logger.info("Creating Administrator role")
            admin_role = Role(
                name='Administrator',
                description='Full system access',
                is_system_role=True,
                created_by='system'  # Set created_by field
            )
            db.session.add(admin_role)

        # Check if Manager role exists
        manager_role = Role.query.filter_by(name='Manager').first()
        if not manager_role:
            logger.info("Creating Manager role")
            manager_role = Role(
                name='Manager',
                description='Project management access',
                is_system_role=True,
                created_by='system'  # Set created_by field
            )
            db.session.add(manager_role)

        # Check if User role exists
        user_role = Role.query.filter_by(name='User').first()
        if not user_role:
            logger.info("Creating User role")
            user_role = Role(
                name='User',
                description='Basic user access',
                is_system_role=True,
                created_by='system'  # Set created_by field
            )
            db.session.add(user_role)

        db.session.commit()
        logger.info("Default roles initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing roles: {str(e)}")
        return False

def init_project_status():
    """Initialize default project statuses if they don't exist."""
    try:
        from app.blueprints.projects.models import ProjectStatus

        # Check if table exists first
        try:
            if not ProjectStatus.query.first():
                logger.info("Creating default project statuses")
                statuses = [
                    ('Not Started', '#dc3545'),  # Red
                    ('In Progress', '#ffc107'),  # Yellow
                    ('On Hold', '#6c757d'),      # Gray
                    ('Completed', '#28a745'),    # Green
                    ('Cancelled', '#343a40')     # Dark
                ]
                for name, color in statuses:
                    status = ProjectStatus(
                        name=name,
                        color=color,
                        created_by='system'
                    )
                    db.session.add(status)
                db.session.commit()
                logger.info("Default project statuses created")
        except OperationalError:
            logger.info("Project status table does not exist yet")
            return True
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project statuses: {str(e)}")
        return False

def init_project_priorities():
    """Initialize default project priorities if they don't exist."""
    try:
        from app.blueprints.projects.models import ProjectPriority

        # Check if table exists first
        try:
            if not ProjectPriority.query.first():
                logger.info("Creating default project priorities")
                priorities = [
                    ('Low', '#28a745'),      # Green
                    ('Medium', '#ffc107'),   # Yellow
                    ('High', '#dc3545'),     # Red
                    ('Critical', '#9c27b0')  # Purple
                ]
                for name, color in priorities:
                    priority = ProjectPriority(
                        name=name,
                        color=color,
                        created_by='system'
                    )
                    db.session.add(priority)
                db.session.commit()
                logger.info("Default project priorities created")
        except OperationalError:
            logger.info("Project priority table does not exist yet")
            return True
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project priorities: {str(e)}")
        return False

def init_database():
    """Initialize database with required data."""
    try:
        with current_app.app_context():
            # Initialize roles first since other parts depend on it
            if not init_roles():
                logger.error("Failed to initialize roles")
                return False
                
            # Initialize project statuses
            if not init_project_status():
                logger.error("Failed to initialize project statuses")
                return False
                
            # Initialize project priorities
            if not init_project_priorities():
                logger.error("Failed to initialize project priorities")
                return False
                
            logger.info("Database initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
