from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justin/Downloads/4th_quarter_2024_flask-blackfridaylunch/app/instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

with app.app_context():
    print("\nProject Statuses:")
    statuses = ProjectStatus.query.all()
    for status in statuses:
        print(f"- {status.name} ({status.color})")
        
    print("\nProject Priorities:")
    priorities = ProjectPriority.query.all()
    for priority in priorities:
        print(f"- {priority.name} ({priority.color})")
