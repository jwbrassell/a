"""
Modular setup utilities for application initialization
"""
import os
import sys
import secrets
import glob
import re
import importlib
import pymysql
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from app import create_app, db
from app.models import (
    Role, User, NavigationCategory, PageRouteMapping,
    UserPreference, UserActivity, PageVisit
)
from app.plugins.projects.models import ProjectStatus, ProjectPriority
from app.plugins.reports.models import DatabaseConnection, ReportView
from app.plugins.dispatch.models import DispatchTeam, DispatchPriority
from app.plugins.documents.models import Document, DocumentCategory, DocumentTag
from app.plugins.weblinks.models import WebLink, WebLinkCategory, WebLinkTag
from app.plugins.handoffs.models import HandoffShift
from app.plugins.oncall.models import Team as OnCallTeam
from app.plugins.admin.models import (
    SystemMetric, ApplicationMetric, UserMetric,
    FeatureUsage, ResourceMetric
)

class SetupConfig:
    """Configuration class for setup options"""
    def __init__(self, 
                 use_mariadb: bool = False,
                 skip_vault: bool = False,
                 skip_plugins: bool = False,
                 env: str = 'dev'):
        self.use_mariadb = use_mariadb
        self.skip_vault = skip_vault
        self.skip_plugins = skip_plugins
        self.env = env
        self.base_dir = Path.cwd()

class DatabaseSetup:
    """Handle database initialization"""
    @staticmethod
    def init_mariadb() -> bool:
        """Initialize MariaDB database and user"""
        try:
            root_password = os.getenv('MYSQL_ROOT_PASSWORD')
            if not root_password:
                print("Error: MYSQL_ROOT_PASSWORD environment variable is required for MariaDB setup")
                return False

            root_connection = pymysql.connect(
                host=os.getenv('DATABASE_HOST', 'localhost'),
                user='root',
                password=root_password,
            )
            
            with root_connection.cursor() as cursor:
                database_name = os.getenv('DATABASE_NAME', 'portal_db')
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
                
                user = os.getenv('DATABASE_USER', 'flask_app_user')
                password = os.getenv('DATABASE_PASSWORD', 'your-password-here')
                
                cursor.execute(f"DROP USER IF EXISTS '{user}'@'localhost'")
                cursor.execute(f"DROP USER IF EXISTS '{user}'@'%'")
                
                cursor.execute(f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}'")
                cursor.execute(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{user}'@'localhost'")
                cursor.execute(f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{user}'@'%'")
                cursor.execute("FLUSH PRIVILEGES")
                
            root_connection.close()
            print(f"Successfully initialized MariaDB database '{database_name}' and user '{user}'")
            return True
            
        except Exception as e:
            print(f"Error initializing MariaDB: {str(e)}")
            print("\nFor MariaDB setup, ensure:")
            print("1. MariaDB is installed and running")
            print("2. You have root access to MariaDB")
            print("3. Set MYSQL_ROOT_PASSWORD environment variable")
            print("4. Configure other DB settings in .env:")
            print("   DATABASE_USER")
            print("   DATABASE_PASSWORD")
            print("   DATABASE_HOST")
            print("   DATABASE_NAME")
            return False

    @staticmethod
    def init_sqlite(base_dir: Path):
        """Initialize SQLite database"""
        instance_path = base_dir / "instance"
        instance_path.mkdir(exist_ok=True)
        print("Created instance directory")
        
        db_path = instance_path / "app.db"
        if db_path.exists():
            db_path.unlink()
            print("Removed existing database")

class EnvironmentSetup:
    """Handle environment configuration"""
    @staticmethod
    def find_nginx_ssl_certs() -> Dict[str, Optional[str]]:
        """Find SSL certificates in nginx configuration"""
        ssl_certs = {'cert': None, 'key': None}
        nginx_conf_dir = '/etc/nginx/conf.d'
        
        if not os.path.exists(nginx_conf_dir):
            return ssl_certs
        
        try:
            conf_files = glob.glob(os.path.join(nginx_conf_dir, '*.conf'))
            
            for conf_file in conf_files:
                with open(conf_file, 'r') as f:
                    content = f.read()
                    cert_match = re.search(r'ssl_certificate\s+(.*?);', content)
                    key_match = re.search(r'ssl_certificate_key\s+(.*?);', content)
                    
                    if cert_match and key_match:
                        cert_path = cert_match.group(1).strip()
                        key_path = key_match.group(1).strip()
                        
                        if os.path.exists(cert_path) and os.path.exists(key_path):
                            ssl_certs['cert'] = cert_path
                            ssl_certs['key'] = key_path
                            break
        except Exception as e:
            print(f"Warning: Error reading nginx configuration: {e}")
        
        return ssl_certs

    @staticmethod
    def create_env_file(config: SetupConfig):
        """Create or update .env file"""
        ssl_certs = EnvironmentSetup.find_nginx_ssl_certs()
        current_dir = config.base_dir
        sqlite_path = current_dir / 'instance' / 'app.db'
        
        redis_config = """
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SSL=False"""

        if ssl_certs['cert'] and ssl_certs['key']:
            redis_config = f"""
# Redis Configuration (with SSL from nginx certificates)
REDIS_URL=rediss://localhost:6379/0
REDIS_SSL=True
REDIS_SSL_CERTFILE={ssl_certs['cert']}
REDIS_SSL_KEYFILE={ssl_certs['key']}"""
        
        if config.use_mariadb:
            env_content = f"""# Flask Configuration
FLASK_APP=app
FLASK_ENV={config.env}
SECRET_KEY={secrets.token_hex(32)}

# Database Type (mariadb or sqlite)
DB_TYPE=mariadb

# MariaDB Configuration
DATABASE_USER=flask_app_user
DATABASE_PASSWORD=default_password
DATABASE_HOST=localhost
DATABASE_NAME=portal_db

# Database Pool Configuration
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_TIMEOUT=20
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_MAX_OVERFLOW=10
{redis_config}"""
        else:
            env_content = f"""# Flask Configuration
FLASK_APP=app
FLASK_ENV={config.env}
SECRET_KEY={secrets.token_hex(32)}

# Database Type (mariadb or sqlite)
DB_TYPE=sqlite

# SQLite Configuration (absolute path)
SQLITE_PATH={sqlite_path}

# Database Pool Configuration
SQLALCHEMY_POOL_SIZE=30
SQLALCHEMY_POOL_TIMEOUT=20
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_MAX_OVERFLOW=10
{redis_config}"""

        env_file = current_dir / '.env'
        env_file.write_text(env_content)
        print(f"{'Created' if not env_file.exists() else 'Updated'} .env file with {config.env} settings")
        
        if ssl_certs['cert'] and ssl_certs['key']:
            print("Found and configured nginx SSL certificates for Redis")

class CoreDataSetup:
    """Handle core data initialization"""
    @staticmethod
    def init_core_data():
        """Initialize core roles and admin user"""
        print("\nInitializing core data...")
        
        # Create admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                notes='Administrator role',
                icon='fa-shield-alt',
                created_by='system',
                created_at=datetime.utcnow()
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                employee_number='ADMIN001',
                name='System Administrator',
                email='admin@example.com',
                vzid='admin',
                roles=[admin_role]
            )
            admin.set_password('test123')
            db.session.add(admin)
            db.session.commit()
        
        # Create other core roles
        roles = [
            {'name': 'user', 'notes': 'Standard user role', 'icon': 'fa-user'},
            {'name': 'manager', 'notes': 'Manager role', 'icon': 'fa-user-tie'}
        ]
        
        for role_data in roles:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(
                    name=role_data['name'],
                    notes=role_data['notes'],
                    icon=role_data['icon'],
                    created_by='system',
                    created_at=datetime.utcnow()
                )
                db.session.add(role)
        
        db.session.commit()
        print("Core data initialized")

    @staticmethod
    def init_navigation():
        """Initialize navigation structure"""
        print("\nInitializing navigation categories...")
        
        categories = [
            {'name': 'Tools', 'icon': 'fa-tools', 'weight': 100},
            {'name': 'Admin', 'icon': 'fa-shield-alt', 'weight': 200},
            {'name': 'Reports', 'icon': 'fa-chart-bar', 'weight': 300}
        ]
        
        for cat_data in categories:
            category = NavigationCategory.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = NavigationCategory(
                    name=cat_data['name'],
                    icon=cat_data['icon'],
                    weight=cat_data['weight'],
                    created_by='system'
                )
                db.session.add(category)
        
        db.session.commit()

        admin_category = NavigationCategory.query.filter_by(name='Admin').first()
        admin_role = Role.query.filter_by(name='admin').first()

        admin_route = PageRouteMapping.query.filter_by(route='/admin').first()
        if not admin_route:
            admin_route = PageRouteMapping(
                page_name='Admin Dashboard',
                route='/admin',
                icon='fa-cogs',
                weight=0,
                category_id=admin_category.id,
                show_in_navbar=True,
                created_by='system'
            )
            admin_route.allowed_roles.append(admin_role)
            db.session.add(admin_route)
        
        monitoring_route = PageRouteMapping.query.filter_by(route='/admin/monitoring').first()
        if not monitoring_route:
            monitoring_route = PageRouteMapping(
                page_name='System Monitoring',
                route='/admin/monitoring',
                icon='fa-chart-line',
                weight=50,
                category_id=admin_category.id,
                show_in_navbar=True,
                created_by='system'
            )
            monitoring_route.allowed_roles.append(admin_role)
            db.session.add(monitoring_route)
        
        db.session.commit()
        print("Navigation categories initialized")

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
        
        statuses = [
            {'name': 'open', 'color': 'secondary'},
            {'name': 'active', 'color': 'primary'},
            {'name': 'in_progress', 'color': 'info'},
            {'name': 'review', 'color': 'warning'},
            {'name': 'completed', 'color': 'success'},
            {'name': 'cancelled', 'color': 'danger'}
        ]
        
        for status_data in statuses:
            status = ProjectStatus.query.filter_by(name=status_data['name']).first()
            if not status:
                status = ProjectStatus(
                    name=status_data['name'],
                    color=status_data['color'],
                    created_by='system'
                )
                db.session.add(status)
        
        priorities = [
            {'name': 'low', 'color': 'success'},
            {'name': 'medium', 'color': 'warning'},
            {'name': 'high', 'color': 'danger'},
            {'name': 'critical', 'color': 'dark'}
        ]
        
        for priority_data in priorities:
            priority = ProjectPriority.query.filter_by(name=priority_data['name']).first()
            if not priority:
                priority = ProjectPriority(
                    name=priority_data['name'],
                    color=priority_data['color'],
                    created_by='system'
                )
                db.session.add(priority)
        
        db.session.commit()
        print("Project data initialized")

    @staticmethod
    def init_dispatch_data():
        """Initialize dispatch data"""
        print("\nInitializing dispatch data...")
        
        teams = [
            {'name': 'Network', 'email': 'network@example.com', 'description': 'Network team'},
            {'name': 'Security', 'email': 'security@example.com', 'description': 'Security team'},
            {'name': 'Support', 'email': 'support@example.com', 'description': 'Support team'}
        ]
        
        for team_data in teams:
            team = DispatchTeam.query.filter_by(name=team_data['name']).first()
            if not team:
                team = DispatchTeam(**team_data)
                db.session.add(team)
        
        priorities = [
            {'name': 'Low', 'color': 'success', 'icon': 'fa-arrow-down'},
            {'name': 'Medium', 'color': 'warning', 'icon': 'fa-arrow-right'},
            {'name': 'High', 'color': 'danger', 'icon': 'fa-arrow-up'},
            {'name': 'Critical', 'color': 'dark', 'icon': 'fa-exclamation'}
        ]
        
        for priority_data in priorities:
            priority = DispatchPriority.query.filter_by(name=priority_data['name']).first()
            if not priority:
                priority = DispatchPriority(**priority_data)
                db.session.add(priority)
        
        db.session.commit()
        print("Dispatch data initialized")

    @staticmethod
    def init_document_data():
        """Initialize document data"""
        print("\nInitializing document data...")
        
        admin = User.query.filter_by(username='admin').first()
        
        categories = [
            {'name': 'General', 'description': 'General documents'},
            {'name': 'Procedures', 'description': 'Procedure documents'},
            {'name': 'Templates', 'description': 'Template documents'},
            {'name': 'Knowledge Base', 'description': 'Knowledge base articles'},
            {'name': 'Guides', 'description': 'User guides and tutorials'}
        ]
        
        for cat_data in categories:
            category = DocumentCategory.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = DocumentCategory(**cat_data)
                db.session.add(category)
        
        db.session.flush()
        
        tags = [
            'Guide', 'Tutorial', 'Reference', 'Policy', 'Template',
            'Important', 'Draft', 'Review', 'Approved', 'Archived'
        ]
        
        for tag_name in tags:
            tag = DocumentTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = DocumentTag(name=tag_name)
                db.session.add(tag)
        
        db.session.flush()
        
        template_category = DocumentCategory.query.filter_by(name='Templates').first()
        template_tag = DocumentTag.query.filter_by(name='Template').first()
        
        templates = [
            {
                'title': 'Standard Procedure Template',
                'content': '''
                <h1>Procedure Title</h1>
                <h2>Purpose</h2>
                <p>[Describe the purpose of this procedure]</p>
                
                <h2>Scope</h2>
                <p>[Define the scope and applicability]</p>
                
                <h2>Prerequisites</h2>
                <ul>
                    <li>Requirement 1</li>
                    <li>Requirement 2</li>
                </ul>
                
                <h2>Procedure Steps</h2>
                <ol>
                    <li>Step 1</li>
                    <li>Step 2</li>
                    <li>Step 3</li>
                </ol>
                
                <h2>References</h2>
                <p>[List any related documents or references]</p>
                ''',
                'template_name': 'Standard Procedure'
            },
            {
                'title': 'Knowledge Base Article Template',
                'content': '''
                <h1>Article Title</h1>
                
                <h2>Overview</h2>
                <p>[Provide a brief overview of the topic]</p>
                
                <h2>Details</h2>
                <p>[Detailed explanation of the topic]</p>
                
                <h2>Common Issues</h2>
                <ul>
                    <li>Issue 1: [Solution]</li>
                    <li>Issue 2: [Solution]</li>
                </ul>
                
                <h2>Related Articles</h2>
                <p>[List related knowledge base articles]</p>
                ''',
                'template_name': 'Knowledge Base Article'
            }
        ]
        
        for template_data in templates:
            template = Document.query.filter_by(title=template_data['title']).first()
            if not template:
                template = Document(
                    title=template_data['title'],
                    content=template_data['content'],
                    category_id=template_category.id,
                    created_by=admin.id,
                    is_template=True,
                    template_name=template_data['template_name']
                )
                template.tags.append(template_tag)
                db.session.add(template)
        
        db.session.commit()
        print("Document data initialized")

    @staticmethod
    def init_weblinks_data():
        """Initialize weblinks data"""
        print("\nInitializing web links data...")
        
        categories = [
            {'name': 'Development', 'created_by': 'system'},
            {'name': 'Documentation', 'created_by': 'system'},
            {'name': 'Tools', 'created_by': 'system'},
            {'name': 'Resources', 'created_by': 'system'}
        ]
        
        for cat_data in categories:
            category = WebLinkCategory.query.filter_by(name=cat_data['name']).first()
            if not category:
                category = WebLinkCategory(**cat_data)
                db.session.add(category)
        
        tags = [
            {'name': 'Reference', 'created_by': 'system'},
            {'name': 'API', 'created_by': 'system'},
            {'name': 'Tutorial', 'created_by': 'system'},
            {'name': 'Guide', 'created_by': 'system'}
        ]
        
        for tag_data in tags:
            tag = WebLinkTag.query.filter_by(name=tag_data['name']).first()
            if not tag:
                tag = WebLinkTag(**tag_data)
                db.session.add(tag)
        
        db.session.commit()
        print("Web links data initialized")

    @staticmethod
    def init_handoff_data():
        """Initialize handoff data"""
        print("\nInitializing handoff data...")
        
        shifts = [
            {'name': '1st', 'description': 'First shift'},
            {'name': '2nd', 'description': 'Second shift'},
            {'name': '3rd', 'description': 'Third shift'}
        ]
        
        for shift_data in shifts:
            shift = HandoffShift.query.filter_by(name=shift_data['name']).first()
            if not shift:
                shift = HandoffShift(**shift_data)
                db.session.add(shift)
        
        db.session.commit()
        print("Handoff data initialized")

    @staticmethod
    def init_oncall_data():
        """Initialize oncall data"""
        print("\nInitializing oncall data...")
        
        teams = [
            {'name': 'Network', 'color': 'primary'},
            {'name': 'Security', 'color': 'danger'},
            {'name': 'Support', 'color': 'success'}
        ]
        
        for team_data in teams:
            team = OnCallTeam.query.filter_by(name=team_data['name']).first()
            if not team:
                team = OnCallTeam(**team_data)
                db.session.add(team)
        
        db.session.commit()
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
                'created_by': admin.id
            }
        ]
        
        for conn_data in connections:
            conn = db.session.query(DatabaseConnection).filter_by(name=conn_data['name']).first()
            if not conn:
                conn = DatabaseConnection(**conn_data)
                db.session.add(conn)
        
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
