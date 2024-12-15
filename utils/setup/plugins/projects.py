"""
Projects plugin setup module
"""
from app.extensions import db
from app.plugins.projects.models import ProjectStatus, ProjectPriority
from utils.setup.plugin_setup import PluginSetup

class ProjectsSetup(PluginSetup):
    """Handle projects plugin initialization"""
    
    def init_data(self):
        """Initialize projects data"""
        admin = db.session.query(db.models.User).filter_by(username='admin').first()
        
        # Initialize default project statuses
        default_statuses = [
            ('Not Started', 'secondary'),
            ('In Progress', 'primary'),
            ('On Hold', 'warning'),
            ('Completed', 'success'),
            ('Cancelled', 'danger')
        ]
        
        for name, color in default_statuses:
            status = ProjectStatus.query.filter_by(name=name).first()
            if not status:
                status = ProjectStatus(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(status)
        
        # Initialize default project priorities
        default_priorities = [
            ('Low', 'info'),
            ('Medium', 'warning'),
            ('High', 'danger'),
            ('Critical', 'dark')
        ]
        
        for name, color in default_priorities:
            priority = ProjectPriority.query.filter_by(name=name).first()
            if not priority:
                priority = ProjectPriority(
                    name=name,
                    color=color,
                    created_by='system'
                )
                db.session.add(priority)
        
        db.session.commit()
    
    def init_navigation(self):
        """Initialize projects navigation"""
        # Add projects section to main navigation
        self.add_route(
            page_name='Projects',
            route='/projects',
            icon='fa-project-diagram',
            category_id=self.main_category.id,
            weight=20,
            roles=['user']  # Available to all users
        )
        
        # Add project management section
        self.add_route(
            page_name='Project Management',
            route='/projects/manage',
            icon='fa-tasks',
            category_id=self.admin_category.id,
            weight=20,
            roles=['admin']  # Admin only
        )
