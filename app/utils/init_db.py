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
        from sqlalchemy import inspect

        # Check if table exists first
        inspector = inspect(db.engine)
        if 'role' not in inspector.get_table_names():
            logger.info("Role table does not exist yet, skipping role initialization")
            return True

        # Initialize default roles
        default_roles = [
            ('Administrator', 'Full system access', True),
            ('Manager', 'Project management access', True),
            ('User', 'Basic user access', True)
        ]

        for name, description, is_system in default_roles:
            try:
                role = Role.query.filter_by(name=name).first()
                if not role:
                    logger.info(f"Creating {name} role")
                    role = Role(
                        name=name,
                        description=description,
                        is_system_role=is_system,
                        created_by='system'
                    )
                    db.session.add(role)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating role {name}: {str(e)}")
                continue

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
        from sqlalchemy import inspect

        # Check if table exists first
        inspector = inspect(db.engine)
        if 'project_status' not in inspector.get_table_names():
            logger.info("Project status table does not exist yet, skipping initialization")
            return True

        # Default statuses
        statuses = [
            ('Not Started', '#dc3545'),  # Red
            ('In Progress', '#ffc107'),  # Yellow
            ('On Hold', '#6c757d'),      # Gray
            ('Completed', '#28a745'),    # Green
            ('Cancelled', '#343a40')     # Dark
        ]

        for name, color in statuses:
            try:
                status = ProjectStatus.query.filter_by(name=name).first()
                if not status:
                    logger.info(f"Creating project status: {name}")
                    status = ProjectStatus(
                        name=name,
                        color=color,
                        created_by='system'
                    )
                    db.session.add(status)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating project status {name}: {str(e)}")
                continue

        logger.info("Default project statuses initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project statuses: {str(e)}")
        return False

def init_project_priorities():
    """Initialize default project priorities if they don't exist."""
    try:
        from app.blueprints.projects.models import ProjectPriority
        from sqlalchemy import inspect

        # Check if table exists first
        inspector = inspect(db.engine)
        if 'project_priority' not in inspector.get_table_names():
            logger.info("Project priority table does not exist yet, skipping initialization")
            return True

        # Default priorities
        priorities = [
            ('Low', '#28a745'),      # Green
            ('Medium', '#ffc107'),   # Yellow
            ('High', '#dc3545'),     # Red
            ('Critical', '#9c27b0')  # Purple
        ]

        for name, color in priorities:
            try:
                priority = ProjectPriority.query.filter_by(name=name).first()
                if not priority:
                    logger.info(f"Creating project priority: {name}")
                    priority = ProjectPriority(
                        name=name,
                        color=color,
                        created_by='system'
                    )
                    db.session.add(priority)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating project priority {name}: {str(e)}")
                continue

        logger.info("Default project priorities initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing project priorities: {str(e)}")
        return False

def init_actions():
    """Initialize default actions if they don't exist."""
    try:
        from app.models.permissions import Action
        from sqlalchemy import inspect

        # Check if table exists first
        inspector = inspect(db.engine)
        if 'action' not in inspector.get_table_names():
            logger.info("Action table does not exist yet, skipping action initialization")
            return True

        # Default actions with their HTTP methods
        default_actions = [
            ('read', 'GET', 'Read access'),
            ('write', 'POST', 'Write access'),
            ('update', 'PUT', 'Update access'),
            ('delete', 'DELETE', 'Delete access'),
            ('list', 'GET', 'List access'),
            ('create', 'POST', 'Create access'),
            ('edit', 'PUT', 'Edit access'),
            ('remove', 'DELETE', 'Remove access')
        ]

        for name, method, description in default_actions:
            try:
                action = Action.query.filter_by(name=name, method=method).first()
                if not action:
                    logger.info(f"Creating action: {name} ({method})")
                    action = Action(
                        name=name,
                        method=method,
                        description=description,
                        created_by='system'
                    )
                    db.session.add(action)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating action {name}: {str(e)}")
                continue

        logger.info("Default actions initialized successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing actions: {str(e)}")
        return False

def init_database():
    """Initialize database with required data."""
    try:
        with current_app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Found tables: {', '.join(tables)}")

            # Initialize core system tables first
            logger.info("Initializing core system tables...")
            if 'action' in tables and not init_actions():
                logger.error("Failed to initialize actions")
                return False

            if 'role' in tables and not init_roles():
                logger.error("Failed to initialize roles")
                return False

            # Initialize plugin tables if they exist
            logger.info("Initializing plugin tables...")
            if 'project_status' in tables and not init_project_status():
                logger.error("Failed to initialize project statuses")
                return False

            if 'project_priority' in tables and not init_project_priorities():
                logger.error("Failed to initialize project priorities")
                return False

            logger.info("Database initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
