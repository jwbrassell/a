#!/usr/bin/env python3
"""
Setup script for initializing the application.
This script:
1. Creates database and tables
2. Initializes core user and role data
3. Then lets plugins attach

Usage:
    python setup.py              # Use SQLite (default)
    python setup.py --mariadb   # Use MariaDB
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import secrets
import multiprocessing
import pymysql
import importlib
import glob
import re
pymysql.install_as_MySQLdb()
from dotenv import load_dotenv
from app import create_app, db
from app.models import (
    Role, User, NavigationCategory, PageRouteMapping,
    UserPreference, UserActivity, PageVisit
)
from app.plugins.projects.models import ProjectStatus, ProjectPriority
from app.plugins.reports.models import DatabaseConnection, ReportView
from app.plugins.dispatch.models import DispatchTeam, DispatchPriority, DispatchTransaction
from app.plugins.documents.models import Document, DocumentCategory, DocumentTag
from app.plugins.weblinks.models import WebLink, WebLinkCategory, WebLinkTag
from app.plugins.handoffs.models import HandoffShift
from app.plugins.oncall.models import Team as OnCallTeam
from app.plugins.admin.models import (
    SystemMetric, ApplicationMetric, UserMetric,
    FeatureUsage, ResourceMetric
)

def find_nginx_ssl_certs():
    """Find SSL certificates in nginx configuration files"""
    ssl_certs = {'cert': None, 'key': None}
    nginx_conf_dir = '/etc/nginx/conf.d'
    
    if not os.path.exists(nginx_conf_dir):
        return ssl_certs
    
    try:
        # Look for .conf files in nginx conf.d directory
        conf_files = glob.glob(os.path.join(nginx_conf_dir, '*.conf'))
        
        for conf_file in conf_files:
            with open(conf_file, 'r') as f:
                content = f.read()
                
                # Look for SSL certificate paths
                cert_match = re.search(r'ssl_certificate\s+(.*?);', content)
                key_match = re.search(r'ssl_certificate_key\s+(.*?);', content)
                
                if cert_match and key_match:
                    cert_path = cert_match.group(1).strip()
                    key_path = key_match.group(1).strip()
                    
                    # Verify files exist
                    if os.path.exists(cert_path) and os.path.exists(key_path):
                        ssl_certs['cert'] = cert_path
                        ssl_certs['key'] = key_path
                        break
    except Exception as e:
        print(f"Warning: Error reading nginx configuration: {e}")
    
    return ssl_certs

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Setup the application database and initial data.')
    parser.add_argument('--mariadb', action='store_true', help='Use MariaDB instead of SQLite')
    return parser.parse_args()

def ensure_env_file(use_mariadb=False):
    """Create .env file with defaults if it doesn't exist"""
    # Get the absolute path for the SQLite database
    current_dir = os.getcwd()
    sqlite_path = os.path.join(current_dir, 'instance', 'app.db')
    
    # Find SSL certificates from nginx if available
    ssl_certs = find_nginx_ssl_certs()
    
    # Base Redis configuration
    redis_config = """
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SSL=False"""

    # If SSL certificates were found, add SSL configuration
    if ssl_certs['cert'] and ssl_certs['key']:
        redis_config = f"""
# Redis Configuration (with SSL from nginx certificates)
REDIS_URL=rediss://localhost:6379/0
REDIS_SSL=True
REDIS_SSL_CERTFILE={ssl_certs['cert']}
REDIS_SSL_KEYFILE={ssl_certs['key']}"""
    
    if use_mariadb:
        env_content = f"""# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
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
FLASK_ENV=development
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
    
    if not os.path.exists('.env'):
        print("Creating default .env file...")
        with open('.env', 'w') as f:
            f.write(env_content)
        print("Created .env file with default settings")
        if ssl_certs['cert'] and ssl_certs['key']:
            print("Found and configured nginx SSL certificates for Redis")
        return True
    else:
        print("Updating existing .env file...")
        with open('.env', 'w') as f:
            f.write(env_content)
        if use_mariadb:
            print("Updated .env file for MariaDB configuration")
        else:
            print(f"Updated .env file with SQLite configuration at: {sqlite_path}")
        if ssl_certs['cert'] and ssl_certs['key']:
            print("Found and configured nginx SSL certificates for Redis")
        return False

def init_mariadb():
    """Initialize MariaDB database and user if they don't exist"""
    try:
        # Check for required environment variables
        root_password = os.getenv('MYSQL_ROOT_PASSWORD')
        if not root_password:
            print("Error: MYSQL_ROOT_PASSWORD environment variable is required for MariaDB setup")
            print("Please set it in your .env file")
            return False

        # Connect to MariaDB as root to create database and user
        root_connection = pymysql.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            user='root',
            password=root_password,
        )
        
        with root_connection.cursor() as cursor:
            # Create database if it doesn't exist
            database_name = os.getenv('DATABASE_NAME', 'portal_db')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
            
            # Create user if it doesn't exist and grant privileges
            user = os.getenv('DATABASE_USER', 'flask_app_user')
            password = os.getenv('DATABASE_PASSWORD', 'your-password-here')
            
            # Drop user if exists to reset privileges (handles password changes)
            cursor.execute(f"DROP USER IF EXISTS '{user}'@'localhost'")
            cursor.execute(f"DROP USER IF EXISTS '{user}'@'%'")
            
            # Create user with password and grant privileges
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

def init_navigation():
    """Initialize navigation categories"""
    print("\nInitializing navigation categories...")
    
    # Create navigation categories
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

    # Get admin category for admin dashboard
    admin_category = NavigationCategory.query.filter_by(name='Admin').first()
    admin_role = Role.query.filter_by(name='admin').first()

    # Create admin dashboard route mapping
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
    
    # Create monitoring dashboard route mapping
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

def init_project_data():
    """Initialize project statuses and priorities"""
    print("\nInitializing project data...")
    
    # Create project statuses
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
    
    # Create project priorities
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

def init_dispatch_data():
    """Initialize dispatch teams and priorities"""
    print("\nInitializing dispatch data...")
    
    # Create dispatch teams
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
    
    # Create dispatch priorities
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

def init_document_data():
    """Initialize document categories and templates"""
    print("\nInitializing document data...")
    
    # Get admin user for created_by reference
    admin = User.query.filter_by(username='admin').first()
    
    # Create document categories
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
    
    db.session.flush()  # Get category IDs
    
    # Create default tags
    tags = [
        'Guide', 'Tutorial', 'Reference', 'Policy', 'Template',
        'Important', 'Draft', 'Review', 'Approved', 'Archived'
    ]
    
    for tag_name in tags:
        tag = DocumentTag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = DocumentTag(name=tag_name)
            db.session.add(tag)
    
    db.session.flush()  # Get tag IDs
    
    # Get categories for templates
    template_category = DocumentCategory.query.filter_by(name='Templates').first()
    
    # Create default document templates
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
    
    template_tag = DocumentTag.query.filter_by(name='Template').first()
    
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

def init_weblinks_data():
    """Initialize web links categories and tags"""
    print("\nInitializing web links data...")
    
    # Create default categories
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
    
    # Create default tags
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

def init_handoff_data():
    """Initialize handoff shifts"""
    print("\nInitializing handoff data...")
    
    # Create default shifts
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

def init_oncall_data():
    """Initialize oncall teams"""
    print("\nInitializing oncall data...")
    
    # Create default teams
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

def init_reports_data():
    """Initialize reports data"""
    print("\nInitializing reports data...")
    
    # Get admin user for created_by reference
    admin = User.query.filter_by(username='admin').first()
    
    # Create default database connections
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
    
    # Get the application DB connection for report views
    app_db = db.session.query(DatabaseConnection).filter_by(name='Application DB').first()
    
    # Create default report views
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

def setup():
    """Run the complete setup process"""
    print("Starting application setup...")
    
    # Parse command line arguments
    args = parse_args()
    
    # Ensure .env file exists with defaults
    env_created = ensure_env_file(use_mariadb=args.mariadb)
    
    # Load environment variables
    load_dotenv()
    
    # Reload config module to pick up new environment variables
    import config
    importlib.reload(config)
    
    # Set DB_TYPE based on arguments
    if args.mariadb:
        os.environ['DB_TYPE'] = 'mariadb'
        print("\nInitializing MariaDB...")
        if not init_mariadb():
            print("\nFailed to initialize MariaDB. Please check the requirements above and try again.")
            sys.exit(1)
    else:
        os.environ['DB_TYPE'] = 'sqlite'
        # Create instance directory if it doesn't exist
        instance_path = "instance"
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print("Created instance directory")
        
        # Always start with a fresh SQLite database
        db_path = os.path.join(instance_path, "app.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database")
    
    # Skip both migrations and plugins initially
    os.environ['SKIP_MIGRATIONS'] = '1'
    os.environ['SKIP_PLUGIN_LOAD'] = '1'
    
    # Create app without plugins first and skip session
    app = create_app(skip_session=True)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("\nCreated database tables")
        
        # Initialize core data first
        init_core_data()
        init_navigation()
    
    # Now enable plugins and reinitialize the app
    os.environ.pop('SKIP_PLUGIN_LOAD', None)
    app = create_app(skip_session=True)
    
    with app.app_context():
        # Initialize plugin data
        init_project_data()
        init_dispatch_data()
        init_document_data()
        init_weblinks_data()
        init_handoff_data()
        init_oncall_data()
        init_reports_data()
    
    print("\nSetup complete!")
    if env_created:
        print("\nNOTE: A new .env file was created with default settings")
        print("You may want to review and update it for your environment")
    
    print("\nYou can now start the application with:")
    print("Development:")
    print("  flask run")
    print("\nProduction:")
    print("  gunicorn -c gunicorn.conf.py wsgi:app")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: test123")

if __name__ == "__main__":
    setup()
