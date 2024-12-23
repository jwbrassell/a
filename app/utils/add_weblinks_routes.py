from flask import current_app
from app.blueprints.weblinks import init_blueprint
from app.models.navigation import PageRouteMapping, NavigationCategory
from app.blueprints.weblinks.init_roles import init_weblinks_roles
from app.extensions import db

def add_weblinks_routes():
    """Add weblinks routes to the application."""
    try:
        # Initialize roles and permissions
        init_weblinks_roles()

        # Initialize and register the blueprint
        weblinks = init_blueprint()
        current_app.register_blueprint(weblinks, url_prefix='/weblinks')

        # Check if route mapping already exists
        existing_route = PageRouteMapping.query.filter_by(route='weblinks.index').first()
        if existing_route:
            return True

        # Get or create Tools category
        tools_category = NavigationCategory.query.filter_by(name='Tools').first()
        if not tools_category:
            tools_category = NavigationCategory(
                name='Tools',
                icon='fa-tools',
                description='Application tools and utilities',
                created_by='system'
            )
            db.session.add(tools_category)
            db.session.commit()

        # Add navigation item
        route_mapping = PageRouteMapping(
            page_name='WebLinks',
            route='weblinks.index',
            icon='fa-link',
            description='Shared web links repository',
            category_id=tools_category.id,
            created_by='system'
        )
        db.session.add(route_mapping)
        db.session.commit()

        return True
    except Exception as e:
        current_app.logger.error(f"Error adding weblinks routes: {e}")
        return False
