from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/app/instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50))
    priority = db.Column(db.String(50))

class ProjectStatus(db.Model):
    __tablename__ = 'project_status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(50), nullable=False)

class ProjectPriority(db.Model):
    __tablename__ = 'project_priority'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(50), nullable=False)

def normalize_database():
    with app.app_context():
        # Normalize status values
        statuses = ProjectStatus.query.all()
        status_mapping = {}
        for status in statuses:
            old_name = status.name
            new_name = old_name.title()  # Convert to title case
            if old_name != new_name:
                status_mapping[old_name] = new_name
                status.name = new_name
                
        # Update project status values
        if status_mapping:
            projects = Project.query.filter(Project.status.in_(status_mapping.keys())).all()
            for project in projects:
                project.status = status_mapping.get(project.status, project.status)

        # Normalize priority values
        priorities = ProjectPriority.query.all()
        priority_mapping = {}
        for priority in priorities:
            old_name = priority.name
            new_name = old_name.title()  # Convert to title case
            if old_name != new_name:
                priority_mapping[old_name] = new_name
                priority.name = new_name
                
        # Update project priority values
        if priority_mapping:
            projects = Project.query.filter(Project.priority.in_(priority_mapping.keys())).all()
            for project in projects:
                project.priority = priority_mapping.get(project.priority, project.priority)

        # Commit changes
        db.session.commit()
        
        print("Database normalized successfully!")
        print("\nCurrent Status Values:")
        for status in ProjectStatus.query.all():
            print(f"- {status.name}")
            
        print("\nCurrent Priority Values:")
        for priority in ProjectPriority.query.all():
            print(f"- {priority.name}")

if __name__ == '__main__':
    normalize_database()
