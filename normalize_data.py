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

def normalize_data():
    with app.app_context():
        # Status mapping
        status_mapping = {
            'open': 'New',
            'in_progress': 'In Progress',
            'review': 'Review',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'archived': 'Archived',
            'on_hold': 'On Hold'
        }

        # Priority mapping
        priority_mapping = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High'
        }

        # Update projects
        projects = Project.query.all()
        for project in projects:
            # Normalize status
            if project.status and project.status.lower() in status_mapping:
                project.status = status_mapping[project.status.lower()]
            
            # Normalize priority
            if project.priority and project.priority.lower() in priority_mapping:
                project.priority = priority_mapping[project.priority.lower()]

        # Commit changes
        db.session.commit()
        print("Data normalized successfully!")

if __name__ == '__main__':
    normalize_data()
