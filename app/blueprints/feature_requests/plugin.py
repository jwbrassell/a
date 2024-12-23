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
                ('read', '*', 'Read access for feature requests'),
                ('write', '*', 'Create feature requests'),
                ('update', '*', 'Update feature requests')
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
            
            # Create and register the regular permission
            permission = Permission.query.filter_by(name='feature_requests').first()
            if not permission:
                permission = Permission(
                    name='feature_requests',
                    description='Access to feature requests functionality',
                    created_by='system'
                )
                db.session.add(permission)
                db.session.flush()

                # Add actions to permission
                for name, _, _ in actions:
                    action = Action.query.filter_by(name=name).first()
                    if action and action not in permission.actions:
                        permission.actions.append(action)

            # Create and register the admin permission
            admin_permission = Permission.query.filter_by(name='feature_requests_admin').first()
            if not admin_permission:
                admin_permission = Permission(
                    name='feature_requests_admin',
                    description='Administrative access to feature requests',
                    created_by='system'
                )
                db.session.add(admin_permission)
                db.session.flush()

                # Add actions to admin permission
                for name, _, _ in actions:
                    action = Action.query.filter_by(name=name).first()
                    if action and action not in admin_permission.actions:
                        admin_permission.actions.append(action)

            # Assign permissions to roles
            admin_role = Role.query.filter_by(name='Administrator').first()
            user_role = Role.query.filter_by(name='User').first()

            if admin_role:
                if permission not in admin_role.permissions:
                    admin_role.permissions.append(permission)
                if admin_permission not in admin_role.permissions:
                    admin_role.permissions.append(admin_permission)
            if user_role and permission not in user_role.permissions:
                user_role.permissions.append(permission)

            db.session.commit()
            app.logger.info("Feature requests permissions initialized successfully")

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error initializing feature requests permissions: {str(e)}")
            raise

    try:
        # Register blueprint first
        app.register_blueprint(bp, url_prefix='/feature_requests')
        app.logger.info("Feature requests blueprint registered with prefix '/feature_requests'")
        
        # Verify routes are registered
        registered_rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith('feature_requests.')]
        if not registered_rules:
            raise Exception("No routes registered for feature_requests blueprint")
        
        # Log registered routes for debugging
        app.logger.info("Registered routes for feature requests blueprint:")
        for rule in registered_rules:
            app.logger.info(f"  Endpoint: {rule.endpoint}")
            app.logger.info(f"  URL Rule: {rule.rule}")
            app.logger.info(f"  Methods: {rule.methods}")
            app.logger.info("---")

        # Define route mappings
        route_mappings = [
            {
                'route': '/feature_requests',
                'page_name': 'Feature Requests',
                'roles': ['Administrator', 'User'],
                'icon': 'fa-lightbulb',
                'weight': 100
            },
            {
                'route': '/feature_requests/admin',
                'page_name': 'Feature Request Admin',
                'roles': ['Administrator'],
                'icon': 'fa-lightbulb',
                'weight': 100,
                'hidden': True
            }
        ]

        # Sync routes for the blueprint
        if not sync_blueprint_routes('feature_requests', route_mappings):
            raise Exception("Failed to sync feature request routes")
        
        app.logger.info("Feature requests routes mapped successfully")
    except Exception as e:
        app.logger.error(f"Error in feature requests initialization: {str(e)}")

    return True
