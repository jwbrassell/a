from datetime import datetime
from app import db
from app.models import User, Role, UserActivity

class ValidationError(Exception):
    """Custom validation error for project models"""
    pass

# Association tables for many-to-many relationships
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

project_roles = db.Table('project_roles',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

# Task dependencies association table
task_dependencies = db.Table('task_dependencies',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('dependency_id', db.Integer, db.ForeignKey('task.id'), primary_key=True)
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
    summary = db.Column(db.String(500))
    icon = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(50))
    priority = db.Column(db.String(50))
    percent_complete = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    
    # Notification settings
    notify_task_created = db.Column(db.Boolean, default=True)
    notify_task_completed = db.Column(db.Boolean, default=True)
    notify_comments = db.Column(db.Boolean, default=True)
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lead = db.relationship('User', foreign_keys=[lead_id])
    watchers = db.relationship('User', secondary=project_watchers, lazy='subquery')
    stakeholders = db.relationship('User', secondary=project_stakeholders, lazy='subquery')
    shareholders = db.relationship('User', secondary=project_shareholders, lazy='subquery')
    roles = db.relationship('Role', secondary=project_roles, lazy='subquery')
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='project', lazy=True, cascade='all, delete-orphan',
                          order_by='Todo.sort_order')
    comments = db.relationship('Comment', backref='project', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('History', backref='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'

    @property
    def status_obj(self):
        """Get the ProjectStatus object for this project's status"""
        if self.status:
            return ProjectStatus.query.filter_by(name=self.status).first()
        return None

    @property
    def priority_obj(self):
        """Get the ProjectPriority object for this project's priority"""
        if self.priority:
            return ProjectPriority.query.filter_by(name=self.priority).first()
        return None

    @property
    def status_class(self):
        """Return Bootstrap class based on status"""
        status = self.status_obj
        return status.color if status else 'secondary'

    @property
    def priority_class(self):
        """Return Bootstrap class based on priority"""
        priority = self.priority_obj
        return priority.color if priority else 'secondary'
    
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
            'watchers': [user.username for user in self.watchers],
            'stakeholders': [user.username for user in self.stakeholders],
            'shareholders': [user.username for user in self.shareholders],
            'roles': [role.name for role in self.roles],
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Task(db.Model):
    """Task model for project tasks"""
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    name = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500))
    description = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey('project_status.id'))
    priority_id = db.Column(db.Integer, db.ForeignKey('project_priority.id'))
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    position = db.Column(db.Integer, default=0)
    list_position = db.Column(db.String(50), default='todo')
    
    # Task depth limit
    MAX_DEPTH = 3
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    status = db.relationship('ProjectStatus', foreign_keys=[status_id])
    priority = db.relationship('ProjectPriority', foreign_keys=[priority_id])
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]),
                             cascade='all, delete-orphan')
    todos = db.relationship('Todo', backref='task', lazy=True, cascade='all, delete-orphan',
                          order_by='Todo.sort_order')
    comments = db.relationship('Comment', backref='task', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('History', backref='task', lazy=True, cascade='all, delete-orphan')
    
    # Task dependencies
    dependencies = db.relationship(
        'Task', secondary=task_dependencies,
        primaryjoin=(task_dependencies.c.task_id == id),
        secondaryjoin=(task_dependencies.c.dependency_id == id),
        backref=db.backref('dependent_tasks', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Task {self.name}>'

    @property
    def status_class(self):
        """Return Bootstrap class based on status"""
        if self.status:
            return self.status.color
        return 'secondary'

    @property
    def priority_class(self):
        """Return Bootstrap class based on priority"""
        if self.priority:
            return self.priority.color
        return 'secondary'
    
    def get_depth(self):
        """Calculate the depth of this task in the hierarchy"""
        depth = 0
        current = self
        while current.parent:
            depth += 1
            current = current.parent
        return depth
    
    def validate_depth(self):
        """Validate task depth doesn't exceed maximum"""
        depth = self.get_depth()
        if depth >= self.MAX_DEPTH:
            raise ValidationError(f"Maximum task depth of {self.MAX_DEPTH} exceeded")
    
    def validate_dependencies(self):
        """Validate task dependencies for circular references"""
        visited = set()
        
        def check_circular(task):
            if task.id in visited:
                raise ValidationError("Circular dependency detected")
            visited.add(task.id)
            for dep in task.dependencies:
                check_circular(dep)
            visited.remove(task.id)
        
        check_circular(self)
    
    @classmethod
    def reorder_tasks(cls, project_id, task_positions):
        """Update task positions in bulk"""
        for position, task_id in enumerate(task_positions):
            cls.query.filter_by(id=task_id, project_id=project_id).update(
                {'position': position}
            )
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'parent_id': self.parent_id,
            'name': self.name,
            'summary': self.summary,
            'description': self.description,
            'status': self.status.name if self.status else None,
            'priority': self.priority.name if self.priority else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_to': self.assigned_to.username if self.assigned_to else None,
            'assigned_to_id': self.assigned_to_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'position': self.position,
            'list_position': self.list_position,
            'depth': self.get_depth(),
            'subtasks': [subtask.to_dict() for subtask in self.subtasks],
            'dependencies': [{'id': t.id, 'name': t.name} for t in self.dependencies],
            'dependent_tasks': [{'id': t.id, 'name': t.name} for t in self.dependent_tasks],
            'history': [h.to_dict() for h in self.history],
            'comments': [c.to_dict() for c in self.comments],
            'todos': [todo.to_dict() for todo in self.todos]  # Added this line
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
    due_date = db.Column(db.Date)
    sort_order = db.Column(db.Integer, default=0)
    
    # Relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])

    def __repr__(self):
        return f'<Todo {self.description[:20]}...>'

    @property
    def badge_color(self):
        """Return Bootstrap color class based on due date and completion status"""
        if self.completed:
            return 'success'
        if not self.due_date:
            return 'secondary'
        
        today = datetime.utcnow().date()
        if self.due_date < today:
            return 'danger'
        elif self.due_date == today:
            return 'warning'
        return 'info'

    @property
    def due_text(self):
        """Return human-readable due date text"""
        if not self.due_date:
            return 'No due date'
        
        today = datetime.utcnow().date()
        if self.due_date < today:
            return 'Overdue'
        elif self.due_date == today:
            return 'Due today'
        else:
            return self.due_date.strftime('%Y-%m-%d')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'description': self.description,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'assigned_to': self.assigned_to.username if self.assigned_to else None,
            'badge_color': self.badge_color,
            'due_text': self.due_text,
            'sort_order': self.sort_order
        }

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
            'user_avatar': self.user.get_preference('avatar', 'images/user_1.jpg') if self.user else None,
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
