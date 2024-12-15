"""
Core data initialization module
"""
from app import db
from app.models import User, Role, PageRouteMapping, NavigationCategory

class CoreDataSetup:
    """Handle core data initialization"""
    @staticmethod
    def init_core_data():
        """Initialize core data like admin user and roles"""
        # Create admin role if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', notes='Administrator', created_by='system')
            db.session.add(admin_role)
            print("Created admin role")

        # Create user role if it doesn't exist
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', notes='Standard User', created_by='system')
            db.session.add(user_role)
            print("Created user role")

        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='Administrator',
                email='admin@example.com',
                is_active=True
            )
            admin.set_password('test123')
            admin.roles.append(admin_role)
            admin.roles.append(user_role)
            db.session.add(admin)
            print("Created admin user")

    @staticmethod
    def init_navigation():
        """Initialize navigation structure"""
        # Create main category if it doesn't exist
        main_category = NavigationCategory.query.filter_by(name='main').first()
        if not main_category:
            main_category = NavigationCategory(
                name='main',
                icon='fa-home',
                description='Main Navigation',
                weight=0,
                created_by='system'
            )
            db.session.add(main_category)

        # Create admin category if it doesn't exist
        admin_category = NavigationCategory.query.filter_by(name='admin').first()
        if not admin_category:
            admin_category = NavigationCategory(
                name='admin',
                icon='fa-cogs',
                description='Admin Navigation',
                weight=100,
                created_by='system'
            )
            db.session.add(admin_category)

        db.session.flush()  # Flush to get category IDs

        nav_items = [
            {
                'page_name': 'Home',
                'route': '/',
                'icon': 'fa-home',
                'category_id': main_category.id,
                'weight': 0,
                'roles': []
            },
            {
                'page_name': 'Profile',
                'route': '/profile',
                'icon': 'fa-user',
                'category_id': main_category.id,
                'weight': 100,
                'roles': []
            },
            {
                'page_name': 'Admin',
                'route': '/admin',
                'icon': 'fa-cogs',
                'category_id': admin_category.id,
                'weight': 0,
                'roles': ['admin']
            }
        ]

        for item in nav_items:
            route = PageRouteMapping.query.filter_by(route=item['route']).first()
            if not route:
                route = PageRouteMapping(
                    page_name=item['page_name'],
                    route=item['route'],
                    icon=item['icon'],
                    category_id=item['category_id'],
                    weight=item['weight'],
                    created_by='system'
                )
                if item['roles']:
                    roles = Role.query.filter(Role.name.in_(item['roles'])).all()
                    route.allowed_roles.extend(roles)
                db.session.add(route)
        print("Initialized navigation structure")
