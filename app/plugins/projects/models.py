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

class ProjectStatus(db.Model):
    """Status configuration for projects"""
    __tablename__ = 'project_status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProjectStatus {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class ProjectPriority(db.Model):
    """Priority configuration for projects"""
    __tablename__ = 'project_priority'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProjectPriority {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class Project(db.Model):
    """Project model for managing projects"""
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500))  # Added summary field
    icon = db.Column(db.String(50))  # Added icon field
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    priority = db.Column(db.String(50), default='medium')
    percent_complete = db.Column(db.Integer, default=0)
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

    @property
    def priority_class(self):
        """Return Bootstrap class based on priority"""
        priority_classes = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger'
        }
        return priority_classes.get(self.priority, 'secondary')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'summary': self.summary,
            'icon': self.icon,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'percent_complete': self.percent_complete,
            'lead': self.lead.username if self.lead else None,
            'team_members': [user.username for user in self.team_members],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Task(db.Model):
    """Task model for project tasks"""
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')
    priority = db.Column(db.String(50), default='medium')
    due_date = db.Column(db.Date)  # Changed from DateTime to Date
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_to': self.assigned_to.username if self.assigned_to else None,
            'assigned_to_id': self.assigned_to_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'history': [h.to_dict() for h in self.history],
            'comments': [c.to_dict() for c in self.comments]
        }

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
    order = db.Column(db.Integer, default=0)  # Added order field for sorting
    
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'content': self.content,
            'user': self.user.username if self.user else None,
            'user_id': self.user_id,
            'user_avatar': self.user.avatar_url if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.username if self.user else None,
            'icon': self.icon,
            'color': self.color
        }
