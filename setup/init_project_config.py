from app import create_app
from app.extensions import db
from app.blueprints.projects.models import ProjectStatus, ProjectPriority
from datetime import datetime

def init_project_config():
    app = create_app()
    with app.app_context():
        # Create default project statuses if they don't exist
        default_statuses = [
            ('Not Started', 'secondary'),
            ('Planning', 'info'),
            ('Active', 'primary'),
            ('On Hold', 'warning'),
            ('Completed', 'success'),
            ('Cancelled', 'danger')
        ]
        
        for status_name, color in default_statuses:
            if not ProjectStatus.query.filter_by(name=status_name).first():
                status = ProjectStatus(
                    name=status_name,
                    color=color,
                    created_by='system'
                )
                db.session.add(status)
                print(f"Created project status: {status_name}")

        # Create default project priorities if they don't exist
        default_priorities = [
            ('Low', 'info'),
            ('Medium', 'warning'),
            ('High', 'danger'),
            ('Critical', 'dark')
        ]
        
        for priority_name, color in default_priorities:
            if not ProjectPriority.query.filter_by(name=priority_name).first():
                priority = ProjectPriority(
                    name=priority_name,
                    color=color,
                    created_by='system'
                )
                db.session.add(priority)
                print(f"Created project priority: {priority_name}")

        db.session.commit()
        print("Project configurations initialized successfully")

if __name__ == '__main__':
    init_project_config()
