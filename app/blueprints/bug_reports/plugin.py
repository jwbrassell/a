from flask import current_app
from .routes import bp
from app.utils.enhanced_rbac import register_permission
from app.models.role import Role
from app.models.permission import Permission
from app.models.permissions import Action
from app.extensions import db
from app.utils.route_manager import sync_blueprint_routes

def init_app(app):
    with app.app_context():
        try:
            # Create actions if they don't exist
            actions = [
                ('read', '*', 'Read access for bug reports'),
                ('write', '*', 'Create bug reports'),
                ('update', '*', 'Update bug reports')
            ]
            for name, method, description in actions:
                action = Action.query.filter_by(name=name).first()
                if not action:
                    action = Action(
                        name=name,
                        method=method,
                        description=description,
                        created_by='system'
                    )
                    db.session.add(action)
            
            # Create and register the permission
            permission = Permission.query.filter_by(name='bug_reports').first()
            if not permission:
                permission = Permission(
                    name='bug_reports',
                    description='Access to bug reports functionality',
                    created_by='system'
                )
                db.session.add(permission)
                db.session.flush()

                # Add actions to permission
                for name, _, _ in actions:
                    action = Action.query.filter_by(name=name).first()
                    if action and action not in permission.actions:
                        permission.actions.append(action)

            # Assign permission to roles
            admin_role = Role.query.filter_by(name='Administrator').first()
            user_role = Role.query.filter_by(name='User').first()

            if admin_role and permission not in admin_role.permissions:
                admin_role.permissions.append(permission)
            if user_role and permission not in user_role.permissions:
                user_role.permissions.append(permission)

            db.session.commit()
            app.logger.info("Bug reports permissions initialized successfully")

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error initializing bug reports permissions: {str(e)}")
            raise

    try:
        # Register blueprint first
        app.register_blueprint(bp, url_prefix='/bug_reports')
        app.logger.info("Bug reports blueprint registered with prefix '/bug_reports'")
        
        # Verify routes are registered
        registered_rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('bug_reports.')]
        if not registered_rules:
            raise Exception("No routes registered for bug_reports blueprint")
        
        # Log registered routes for debugging
        app.logger.info("Registered routes for bug reports blueprint:")
        for rule in registered_rules:
            app.logger.info(f"  Endpoint: {rule.endpoint}")
            app.logger.info(f"  URL Rule: {rule.rule}")
            app.logger.info(f"  Methods: {rule.methods}")
            app.logger.info("---")

        # Define route mappings
        route_mappings = [
            {
                'route': '/bug_reports',
                'page_name': 'Bug Reports',
                'roles': ['Administrator', 'User'],
                'icon': 'fa-bug',
                'weight': 100
            },
            {
                'route': '/bug_reports/reports',
                'page_name': 'Bug Report API',
                'roles': ['Administrator', 'User'],
                'icon': 'fa-bug',
                'weight': 100,
                'hidden': True
            }
        ]

        # Sync routes for the blueprint (use underscore format as per route_manager.py)
        if not sync_blueprint_routes('bug_reports', route_mappings):
            raise Exception("Failed to sync bug report routes")
        
        app.logger.info("Bug reports routes mapped successfully")
    except Exception as e:
        app.logger.error(f"Error in bug reports initialization: {str(e)}")

    return True
