from app.extensions import db
from app.models.role import Role
from app.models.permission import Permission
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_weblinks_roles():
    """Initialize roles and permissions for weblinks."""
    try:
        # Create edit_links permission if it doesn't exist
        edit_links_perm = Permission.query.filter_by(name='edit_links').first()
        if not edit_links_perm:
            edit_links_perm = Permission.create_permission(
                name='edit_links',
                description='Can create and edit weblinks',
                category='weblinks',
                created_by='system'
            )
            logger.info("Created edit_links permission")
        
        # Add permission to admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role and edit_links_perm not in admin_role.permissions:
            admin_role.permissions.append(edit_links_perm)
            logger.info("Added edit_links permission to admin role")
        
        # Create WebLinks Editor role if it doesn't exist
        weblinks_editor = Role.query.filter_by(name='WebLinks Editor').first()
        if not weblinks_editor:
            weblinks_editor = Role(
                name='WebLinks Editor',
                description='Can manage shared weblinks',
                icon='fas fa-link',
                created_by='system',
                is_system_role=True  # Make it a system role
            )
            weblinks_editor.permissions.append(edit_links_perm)
            db.session.add(weblinks_editor)
            logger.info("Created WebLinks Editor role")
        elif edit_links_perm not in weblinks_editor.permissions:
            weblinks_editor.permissions.append(edit_links_perm)
            logger.info("Added edit_links permission to WebLinks Editor role")
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error initializing weblinks roles: {e}")
        db.session.rollback()
        return False
