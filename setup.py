#!/usr/bin/env python3
"""
Setup script for initializing the application.
This script:
1. Creates database and tables
2. Initializes core user and role data
3. Then lets plugins attach
"""

import os
from datetime import datetime
from app import create_app, db
from app.models import Role, User, NavigationCategory, PageRouteMapping
from app.plugins.projects.models import ProjectStatus, ProjectPriority
from app.plugins.reports.models import DatabaseConnection, ReportView
from app.plugins.dispatch.models import DispatchTeam, DispatchPriority, DispatchTransaction
from app.plugins.documents.models import Document, DocumentCategory
from app.plugins.weblinks.models import WebLink, WebLinkCategory, WebLinkTag

def init_core_data():
    """Initialize core roles and admin user"""
    print("\nInitializing core data...")
    
    # Create admin role
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
        category = NavigationCategory(
            name=cat_data['name'],
            icon=cat_data['icon'],
            weight=cat_data['weight'],
            created_by='system'
        )
        db.session.add(category)
    
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
        priority = DispatchPriority(**priority_data)
        db.session.add(priority)
    
    db.session.commit()
    print("Dispatch data initialized")

def init_document_data():
    """Initialize document categories"""
    print("\nInitializing document data...")
    
    # Create document categories
    categories = [
        {'name': 'General', 'description': 'General documents'},
        {'name': 'Procedures', 'description': 'Procedure documents'},
        {'name': 'Templates', 'description': 'Template documents'}
    ]
    
    for cat_data in categories:
        category = DocumentCategory(**cat_data)
        db.session.add(category)
    
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
        tag = WebLinkTag(**tag_data)
        db.session.add(tag)
    
    db.session.commit()
    print("Web links data initialized")

def setup():
    """Run the complete setup process"""
    print("Starting application setup...")
    
    # Create instance directory if it doesn't exist
    instance_path = "instance"
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print("Created instance directory")
    
    # Always start with a fresh database
    db_path = os.path.join(instance_path, "app.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database")
    
    # Skip both migrations and plugins for initial setup
    os.environ['SKIP_MIGRATIONS'] = '1'
    os.environ['SKIP_PLUGIN_LOAD'] = '1'
    
    # Create app without migrations or plugins
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("\nCreated database tables")
        
        # Initialize core data
        init_core_data()
        
        # Initialize navigation categories
        init_navigation()
        
        # Initialize plugin data
        init_project_data()
        init_dispatch_data()
        init_document_data()
        init_weblinks_data()
    
    # Now enable plugins but still skip migrations
    os.environ.pop('SKIP_PLUGIN_LOAD', None)
    app = create_app()
    
    print("\nSetup complete!")
    print("\nYou can now start the application with:")
    print("flask run")
    print("\nDefault admin credentials:")
    print("Username: admin")
    print("Password: test123")

if __name__ == "__main__":
    setup()
