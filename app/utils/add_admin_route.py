from app.extensions import db
from app import create_app
from app.models import NavigationCategory, PageRouteMapping, Role
from sqlalchemy import inspect
import logging

logger = logging.getLogger(__name__)

def add_admin_routes():
    """Add admin dashboard routes to navigation under Admin category."""
    try:
        app = create_app()
        with app.app_context():
            # Check if required tables exist
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            required_tables = ['navigation_category', 'page_route_mapping', 'role']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                logger.info(f"Skipping admin routes initialization - missing tables: {', '.join(missing_tables)}")
                return True

            # Get or create Admin category
            try:
                admin_category = NavigationCategory.query.filter_by(name='Admin').first()
                if not admin_category:
                    logger.info("Creating Admin category")
                    admin_category = NavigationCategory(
                        name='Admin',
                        description='Administrative functions',
                        icon='fa-shield-alt',
                        weight=100,  # High weight to appear at the bottom
                        created_by='system'
                    )
                    db.session.add(admin_category)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating Admin category: {e}")
                return False

            # Get admin role
            try:
                admin_role = Role.query.filter_by(name='Administrator').first()
                if not admin_role:
                    logger.error("Administrator role not found")
                    return False
            except Exception as e:
                logger.error(f"Error getting Administrator role: {e}")
                return False

            # Add admin dashboard route if it doesn't exist
            try:
                admin_route = PageRouteMapping.query.filter_by(route='admin/index').first()
                if not admin_route:
                    logger.info("Creating admin dashboard route")
                    admin_route = PageRouteMapping(
                        page_name='Admin Dashboard',
                        route='admin/index',
                        icon='fa-tachometer-alt',
                        weight=0,  # First item in Admin category
                        category_id=admin_category.id,
                        created_by='system'
                    )
                    admin_route.allowed_roles.append(admin_role)
                    db.session.add(admin_route)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating admin route: {e}")
                return False

            logger.info("Successfully initialized admin routes")
            return True
    except Exception as e:
        logger.error(f"Error in add_admin_routes: {e}")
        return False

if __name__ == '__main__':
    add_admin_routes()
