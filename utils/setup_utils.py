"""
Modular setup utilities for application initialization
"""
from pathlib import Path
import os
import sys
from app import db
from app.models import User, Role, PageRouteMapping, NavigationCategory
from app.plugins.reports.models import DatabaseConnection, ReportView
from app.plugins.reports.vault_utils import vault_manager

class SetupConfig:
    """Configuration class for setup process"""
    def __init__(self, use_mariadb=False, skip_vault=False, skip_plugins=False, env='dev'):
        self.use_mariadb = use_mariadb
        self.skip_vault = skip_vault
        self.skip_plugins = skip_plugins
        self.env = env
        self.base_dir = Path(__file__).resolve().parent.parent

class DatabaseSetup:
    """Handle database initialization"""
    @staticmethod
    def init_sqlite(base_dir):
        """Initialize SQLite database"""
        instance_dir = base_dir / 'instance'
        if not instance_dir.exists():
            instance_dir.mkdir()
        print("\nInitialized SQLite database")
        return True

    @staticmethod
    def init_mariadb():
        """Initialize MariaDB database"""
        try:
            import pymysql
            return True
        except ImportError:
            print("\nError: pymysql not installed. Required for MariaDB support.")
            print("Install with: pip install pymysql")
            return False

class EnvironmentSetup:
    """Handle environment configuration"""
    @staticmethod
    def create_env_file(config: SetupConfig):
        """Create .env file with default settings if it doesn't exist"""
        env_path = config.base_dir / '.env'
        if not env_path.exists():
            with env_path.open('w') as f:
                f.write(f"FLASK_ENV={config.env}\n")
                f.write("FLASK_APP=app.py\n")
                f.write("SECRET_KEY=dev\n")
                if config.use_mariadb:
                    f.write("DB_TYPE=mariadb\n")
                    f.write("MARIADB_USER=root\n")
                    f.write("MARIADB_PASSWORD=\n")
                    f.write("MARIADB_HOST=localhost\n")
                    f.write("MARIADB_PORT=3306\n")
                    f.write("MARIADB_DATABASE=app\n")
                else:
                    f.write("DB_TYPE=sqlite\n")
            print("\nCreated .env file with default settings")

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

class PluginDataSetup:
    """Handle plugin data initialization"""
    @staticmethod
    def init_all_plugin_data():
        """Initialize all plugin data"""
        PluginDataSetup.init_project_data()
        PluginDataSetup.init_dispatch_data()
        PluginDataSetup.init_document_data()
        PluginDataSetup.init_weblinks_data()
        PluginDataSetup.init_handoff_data()
        PluginDataSetup.init_oncall_data()
        PluginDataSetup.init_reports_data()

    @staticmethod
    def init_project_data():
        """Initialize project data"""
        print("\nInitializing project data...")
        from app.plugins.projects.models import ProjectStatus, ProjectPriority
        
        # Create default statuses
        statuses = [
            ('New', 'primary', 0),
            ('In Progress', 'info', 1),
            ('On Hold', 'warning', 2),
            ('Completed', 'success', 3),
            ('Cancelled', 'danger', 4)
        ]
        
        for name, color, weight in statuses:
            status = ProjectStatus.query.filter_by(name=name).first()
            if not status:
                status = ProjectStatus(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(status)
        
        # Create default priorities
        priorities = [
            ('Low', 'secondary', 0),
            ('Medium', 'primary', 1),
            ('High', 'warning', 2),
            ('Critical', 'danger', 3)
        ]
        
        for name, color, weight in priorities:
            priority = ProjectPriority.query.filter_by(name=name).first()
            if not priority:
                priority = ProjectPriority(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(priority)
        
        print("Project data initialized")

    @staticmethod
    def init_dispatch_data():
        """Initialize dispatch data"""
        print("\nInitializing dispatch data...")
        # Add dispatch data initialization here
        print("Dispatch data initialized")

    @staticmethod
    def init_document_data():
        """Initialize document data"""
        print("\nInitializing document data...")
        # Add document data initialization here
        print("Document data initialized")

    @staticmethod
    def init_weblinks_data():
        """Initialize weblinks data"""
        print("\nInitializing weblinks data...")
        # Add weblinks data initialization here
        print("Weblinks data initialized")

    @staticmethod
    def init_handoff_data():
        """Initialize handoff data"""
        print("\nInitializing handoff data...")
        # Add handoff data initialization here
        print("Handoff data initialized")

    @staticmethod
    def init_oncall_data():
        """Initialize oncall data"""
        print("\nInitializing oncall data...")
        # Add oncall data initialization here
        print("Oncall data initialized")

    @staticmethod
    def init_reports_data():
        """Initialize reports data"""
        print("\nInitializing reports data...")
        
        admin = User.query.filter_by(username='admin').first()
        
        connections = [
            {
                'name': 'Application DB',
                'description': 'Main application database',
                'db_type': 'sqlite',
                'database': 'instance/app.db',
                'created_by': admin.id,
                'username': None,  # SQLite doesn't need credentials
                'vault_credentials': {
                    'password': None  # SQLite doesn't need credentials
                }
            }
        ]
        
        for conn_data in connections:
            conn = db.session.query(DatabaseConnection).filter_by(name=conn_data['name']).first()
            if not conn:
                # Create database connection without credentials
                conn = DatabaseConnection(
                    name=conn_data['name'],
                    description=conn_data['description'],
                    db_type=conn_data['db_type'],
                    database=conn_data['database'],
                    username=conn_data['username'],
                    created_by=conn_data['created_by']
                )
                db.session.add(conn)
                db.session.flush()  # Flush to get the ID
                
                # Store credentials in vault if provided
                if conn_data['vault_credentials']:
                    try:
                        vault_manager.store_database_credentials(
                            conn.id,
                            conn_data['vault_credentials']
                        )
                    except Exception as e:
                        print(f"Warning: Failed to store credentials in vault: {e}")
                        print("You may need to manually add credentials later")
        
        db.session.commit()
        
        app_db = db.session.query(DatabaseConnection).filter_by(name='Application DB').first()
        
        views = [
            {
                'title': 'Active Users',
                'description': 'List of all active users in the system',
                'database_id': app_db.id,
                'query': 'SELECT username, name, email FROM user WHERE is_active = 1',
                'column_config': {
                    'username': {'label': 'Username'},
                    'name': {'label': 'Full Name'},
                    'email': {'label': 'Email Address'}
                },
                'is_private': False,
                'created_by': admin.id
            }
        ]
        
        for view_data in views:
            view = db.session.query(ReportView).filter_by(title=view_data['title']).first()
            if not view:
                view = ReportView(**view_data)
                db.session.add(view)
        
        db.session.commit()
        print("Reports data initialized")
