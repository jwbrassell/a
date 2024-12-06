from datetime import datetime
from app import db
from app.models import User

# Association tables for many-to-many relationships
project_team_members = db.Table('project_team_members',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

project_watchers = db.Table('project_watchers',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

project_stakeholders = db.Table('project_stakeholders',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

project_shareholders = db.Table('project_shareholders',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Project(db.Model):
    """Project model for managing projects"""
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notification settings
    notify_task_created = db.Column(db.Boolean, default=True)
    notify_task_completed = db.Column(db.Boolean, default=True)
    notify_comments = db.Column(db.Boolean, default=True)
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lead = db.relationship('User', foreign_keys=[lead_id])
    team_members = db.relationship('User', secondary=project_team_members, lazy='subquery')
    watchers = db.relationship('User', secondary=project_watchers, lazy='subquery')
    stakeholders = db.relationship('User', secondary=project_stakeholders, lazy='subquery')
    shareholders = db.relationship('User', secondary=project_shareholders, lazy='subquery')
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='project', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='project', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('History', backref='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'

    @property
    def status_class(self):
        """Return Bootstrap class based on status"""
        status_classes = {
            'planning': 'info',
            'active': 'success',
            'on_hold': 'warning',
            'completed': 'secondary',
            'archived': 'dark'
        }
        return status_classes.get(self.status, 'secondary')

class Task(db.Model):
    """Task model for project tasks"""
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')
    priority = db.Column(db.String(50), default='medium')
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    todos = db.relationship('Todo', backref='task', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('History', backref='task', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Task {self.name}>'

    @property
    def status_class(self):
        """Return Bootstrap class based on status"""
        status_classes = {
            'open': 'secondary',
            'in_progress': 'primary',
            'review': 'info',
            'completed': 'success'
        }
        return status_classes.get(self.status, 'secondary')

    @property
    def priority_class(self):
        """Return Bootstrap class based on priority"""
        priority_classes = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger'
        }
        return priority_classes.get(self.priority, 'secondary')

class Todo(db.Model):
    """Todo model for checklist items"""
    __tablename__ = 'todo'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    description = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

    def __repr__(self):
        return f'<Todo {self.description[:20]}...>'

class Comment(db.Model):
    """Comment model for projects and tasks"""
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'

class History(db.Model):
    """History model for tracking all changes"""
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)  # 'project', 'task', 'todo'
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    action = db.Column(db.String(50), nullable=False)  # 'created', 'updated', 'deleted'
    details = db.Column(db.JSON)  # Store changes in JSON format
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])

    def __repr__(self):
        return f'<History {self.entity_type}:{self.action}>'

    @property
    def icon(self):
        """Return FontAwesome icon based on action"""
        icons = {
            'created': 'plus',
            'updated': 'edit',
            'deleted': 'trash',
            'completed': 'check',
            'archived': 'archive'
        }
        return icons.get(self.action, 'circle')

    @property
    def color(self):
        """Return Bootstrap color based on action"""
        colors = {
            'created': 'success',
            'updated': 'info',
            'deleted': 'danger',
            'completed': 'success',
            'archived': 'secondary'
        }
        return colors.get(self.action, 'secondary')
